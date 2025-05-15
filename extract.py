# 재시작된 환경에서 다시 실행
import cv2
import numpy as np
import matplotlib.pyplot as plt

# 이미지 재로드
#image_path = "lg-2267728-aug-beethoven--page-2.png"
image_path = "images/lg-5230237-aug-emmentaler--page-3.png"
# image_path = "lg-2267728-aug-gutenberg1939--page-2.png"

image = cv2.imread(image_path)

# 1. 그레이스케일 변환
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 2. Adaptive Thresholding으로 이진화
binary = cv2.adaptiveThreshold(
    gray, 255,
    cv2.ADAPTIVE_THRESH_MEAN_C,
    cv2.THRESH_BINARY_INV,
    blockSize=15,
    C=10
)

# 3. 수평선 검출 커널 (가늘고 긴 수평선만 검출)
horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (80, 1))
staff_candidates = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)

# 4. Contour 기반 필터링: 긴 수평선만 선택
contours, _ = cv2.findContours(staff_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
staff_mask = np.zeros_like(binary)

for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 0.7 * binary.shape[1] and h < 4:
        cv2.drawContours(staff_mask, [cnt], -1, 255, -1)

# 5. 오선 제거
no_staff = cv2.subtract(binary, staff_mask)

# 6. 반전하여 흰 배경 + 검은 기호로
final_result = cv2.bitwise_not(no_staff)

# 저장
final_path_filtered = "no_staff_lines_filtered.png"
cv2.imwrite(final_path_filtered, final_result)

# 시각화
plt.imshow(final_result, cmap='gray')
plt.title("Improved Staff Line Removal (Symbols Preserved)")
plt.axis('off')
plt.show()
