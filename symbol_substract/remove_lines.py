import os
import cv2
import numpy as np

# 입력 폴더 설정 (png 이미지가 저장된 폴더)
input_folder = "images"
output_folder = "removed_staff_lines"
os.makedirs(output_folder, exist_ok=True)

# 처리된 이미지 수 카운트
total_detected = 0

# 모든 PNG 파일 처리
for filename in os.listdir(input_folder):
    if filename.lower().endswith(".png"):
        image_path = os.path.join(input_folder, filename)
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 이진화 및 오선 제거
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                       cv2.THRESH_BINARY_INV, 15, 10)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (60, 1))
        staff_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
        contours, _ = cv2.findContours(staff_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        staff_mask = np.zeros_like(binary)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 0.7 * binary.shape[1] and h < 4:
                cv2.drawContours(staff_mask, [cnt], -1, 255, -1)
        no_staff = cv2.subtract(binary, staff_mask)
        final_result = cv2.bitwise_not(no_staff)

        cv2.imwrite(os.path.join(output_folder, filename+'.png'), final_result)


total_detected
