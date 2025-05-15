import cv2
import numpy as np
import os
from pathlib import Path

# 경로 설정
INPUT_DIR = "images"
OUTPUT_DIR = "special_symbol_candidates"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def remove_staff_lines(gray_img):
    """오선 제거 함수"""
    binary = cv2.adaptiveThreshold(gray_img, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 15, 10)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (60, 1))
    detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    contours, _ = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    staff_mask = np.zeros_like(binary)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 0.7 * gray_img.shape[1] and h < 4:
            cv2.drawContours(staff_mask, [cnt], -1, 255, -1)

    no_staff = cv2.subtract(binary, staff_mask)
    return cv2.bitwise_not(no_staff)

def extract_symbols_from_image(image_path, save_prefix):
    gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        print(f"이미지 로드 실패: {image_path}")
        return 0

    # 1. 오선 제거
    cleaned = remove_staff_lines(gray)

    # 2. 이진화 및 팽창
    _, binary = cv2.threshold(cleaned, 127, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(binary, kernel, iterations=1)

    # 3. 컨투어 찾기
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    count = 0
    for i, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        rect_area = w * h
        if rect_area == 0:
            continue
        extent = area / rect_area
        aspect_ratio = w / h if h > 0 else 0

        # 추상화된 조건
        if 10 < w < 60 and 10 < h < 60 and 0.3 < extent < 0.95 and 0.5 < aspect_ratio < 2.5:
            crop = cleaned[y:y+h, x:x+w]
            max_side = max(crop.shape)
            padded = np.ones((max_side, max_side), dtype=np.uint8) * 255
            y_offset = (max_side - crop.shape[0]) // 2
            x_offset = (max_side - crop.shape[1]) // 2
            padded[y_offset:y_offset+crop.shape[0], x_offset:x_offset+crop.shape[1]] = crop
            resized = cv2.resize(padded, (64, 64))

            outname = f"{save_prefix}_symbol_{count:03}.png"
            cv2.imwrite(os.path.join(OUTPUT_DIR, outname), resized)
            count += 1

    return count

def extract_rest_candidates(image_path, save_prefix):
    gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        print(f"이미지 로드 실패: {image_path}")
        return 0

    cleaned = remove_staff_lines(gray)
    _, binary = cv2.threshold(cleaned, 127, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(binary, kernel, iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    count = 0
    for i, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        rect_area = w * h
        if rect_area == 0:
            continue
        extent = area / rect_area
        aspect_ratio = w / h if h > 0 else 0

        # 온쉼표/이분쉼표 특징: 사각형, 가로 긴 블럭, 면적 빽빽함
        if 8 < w < 40 and 4 < h < 20 and 0.6 < extent <= 1.0 and 1.2 < aspect_ratio < 3.5:
            crop = cleaned[y:y+h, x:x+w]
            max_side = max(crop.shape)
            padded = np.ones((max_side, max_side), dtype=np.uint8) * 255
            y_offset = (max_side - crop.shape[0]) // 2
            x_offset = (max_side - crop.shape[1]) // 2
            padded[y_offset:y_offset+crop.shape[0], x_offset:x_offset+crop.shape[1]] = crop
            resized = cv2.resize(padded, (64, 64))

            outname = f"{save_prefix}_rest_{count:03}.png"
            cv2.imwrite(os.path.join(OUTPUT_DIR, outname), resized)
            count += 1

    return count

# 전체 폴더 반복 처리
total_found = 0
for fname in os.listdir(INPUT_DIR):
    if fname.lower().endswith('.png'):
        fpath = os.path.join(INPUT_DIR, fname)
        prefix = Path(fname).stem
        # found = extract_symbols_from_image(fpath, prefix)
        found = extract_rest_candidates(fpath, prefix)
        print(f"{fname}: {found}개 추출됨")
        total_found += found

print(f"\n🎉 오선 제거 후 총 추출된 기호 수: {total_found}")
