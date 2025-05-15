import cv2
import numpy as np
import os

# 1. 이미지 로드 및 오선 제거
original_path = "images/lg-5230237-aug-emmentaler--page-3.png"
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

# 2. 이진화 + 팽창 (줄기 강조)
_, binary2 = cv2.threshold(final_result, 127, 255, cv2.THRESH_BINARY_INV)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
dilated = cv2.dilate(binary2, kernel, iterations=2)

# 3. 컨투어 추출 및 음표 특성 필터링
contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

note_crops_dir = "note_symbols_improved"
os.makedirs(note_crops_dir, exist_ok=True)

note_count = 0
for i, cnt in enumerate(contours):
    x, y, w, h = cv2.boundingRect(cnt)
    aspect_ratio = w / h if h > 0 else 0
    area = cv2.contourArea(cnt)
    rect_area = w * h
    extent = area / rect_area if rect_area > 0 else 0

    # 음표 기준: 줄기를 고려한 높이, 넓이, 면적, 종횡비
    if 10 < w < 80 and 20 < h < 120 and 0.2 < extent < 0.95 and 0.1 < aspect_ratio < 1.2:
        crop = final_result[y:y+h, x:x+w]

        # 비율 유지하며 padding → 64x64 크기로
        max_side = max(crop.shape)
        padded = np.ones((max_side, max_side), dtype=np.uint8) * 255
        y_offset = (max_side - crop.shape[0]) // 2
        x_offset = (max_side - crop.shape[1]) // 2
        padded[y_offset:y_offset+crop.shape[0], x_offset:x_offset+crop.shape[1]] = crop

        resized = cv2.resize(padded, (64, 64))
        filename = f"note_{note_count:04}.png"
        cv2.imwrite(os.path.join(note_crops_dir, filename), resized)
        note_count += 1

note_count
