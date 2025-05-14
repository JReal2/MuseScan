import os
import cv2
import numpy as np

# 입력 폴더 설정 (png 이미지가 저장된 폴더)
input_folder = "images"
output_folder = "extracted_notes_from_folder"
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

        # 팽창 → 줄기 포함
        _, binary2 = cv2.threshold(final_result, 127, 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(binary2, kernel, iterations=2)

        # 컨투어 추출
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        note_count = 0
        for i, cnt in enumerate(contours):
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / h if h > 0 else 0
            area = cv2.contourArea(cnt)
            rect_area = w * h
            extent = area / rect_area if rect_area > 0 else 0

            # 필터 조건
            if 10 < w < 90 and 20 < h < 120 and 0.25 < extent < 0.95 and 0.1 < aspect_ratio < 1.4:
                crop = final_result[y:y+h, x:x+w]
                max_side = max(crop.shape)
                padded = np.ones((max_side, max_side), dtype=np.uint8) * 255
                y_offset = (max_side - crop.shape[0]) // 2
                x_offset = (max_side - crop.shape[1]) // 2
                padded[y_offset:y_offset+crop.shape[0], x_offset:x_offset+crop.shape[1]] = crop
                resized = cv2.resize(padded, (64, 64))
                outname = f"{os.path.splitext(filename)[0]}_note_{note_count:03}.png"
                cv2.imwrite(os.path.join(output_folder, outname), resized)
                note_count += 1

        total_detected += note_count

total_detected
