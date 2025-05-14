import cv2
import numpy as np
import os

# 1. 이미지 로드 및 오선 제거
original_path = "no_staff_lines_filtered.png"
image = cv2.imread(original_path)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
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

# 2. 쉼표만 추출: 일반적으로 쉼표는 작고 복잡한 모양 (작은 크기, 낮은 외접률)
_, binary2 = cv2.threshold(final_result, 127, 255, cv2.THRESH_BINARY_INV)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
dilated = cv2.dilate(binary2, kernel, iterations=1)
contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 3. 쉼표 특성에 기반한 후보 필터링: 크기 작고, 면적이 꽉 차지 않음
rest_crops_dir = "rest_symbol_crops"
os.makedirs(rest_crops_dir, exist_ok=True)

rest_count = 0
for i, cnt in enumerate(contours):
    x, y, w, h = cv2.boundingRect(cnt)
    area = cv2.contourArea(cnt)
    rect_area = w * h
    extent = area / rect_area if rect_area > 0 else 0

    if 8 < w < 40 and 10 < h < 45 and extent < 0.45:
        crop = final_result[y:y+h, x:x+w]
        resized = cv2.resize(crop, (64, 64))
        filename = f"rest_{rest_count:04}.png"
        cv2.imwrite(os.path.join(rest_crops_dir, filename), resized)
        rest_count += 1

rest_count
