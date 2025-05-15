import cv2
import os
import numpy as np
from ultralytics import YOLO

# 1. 오선 제거
def remove_staff_lines(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (image.shape[1] // 15, 1))
    detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    no_staff = cv2.bitwise_and(binary, binary, mask=cv2.bitwise_not(detected_lines))
    no_staff = cv2.bitwise_not(no_staff)
    return cv2.cvtColor(no_staff, cv2.COLOR_GRAY2BGR)

# 2. 이미지 분할 및 위치 저장
def split_image_with_offsets(image, patch_size=(640, 640), stride=(480, 480)):
    h, w = image.shape[:2]
    pw, ph = patch_size
    sw, sh = stride

    patches = []
    positions = []
    for y in range(0, h - ph + 1, sh):
        for x in range(0, w - pw + 1, sw):
            patch = image[y:y+ph, x:x+pw]
            patches.append(patch)
            positions.append((x, y))
    return patches, positions

# 3. YOLO 추론 실행
def run_yolo_on_patches(model, patches, conf=0.25):
    results_all = []
    for patch in patches:
        result = model.predict(source=patch, conf=conf, verbose=False)
        results_all.append(result[0])  # 1개 이미지라 [0]
    return results_all

# 4. 결과 원본 좌표계로 복원
def restore_to_original_coords(results, positions, patch_size):
    final_boxes = []
    pw, ph = patch_size
    for result, (x_off, y_off) in zip(results, positions):
        if result.boxes is None:
            continue
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            # 원본 좌표로 이동
            final_boxes.append({
                'cls': cls,
                'conf': conf,
                'x1': x1 + x_off,
                'y1': y1 + y_off,
                'x2': x2 + x_off,
                'y2': y2 + y_off
            })
    return final_boxes

# 5. 간단한 NMS (IOU 기반)
def iou(boxA, boxB):
    xa = max(boxA['x1'], boxB['x1'])
    ya = max(boxA['y1'], boxB['y1'])
    xb = min(boxA['x2'], boxB['x2'])
    yb = min(boxA['y2'], boxB['y2'])
    interArea = max(0, xb - xa + 1) * max(0, yb - ya + 1)
    boxAArea = (boxA['x2'] - boxA['x1'] + 1) * (boxA['y2'] - boxA['y1'] + 1)
    boxBArea = (boxB['x2'] - boxB['x1'] + 1) * (boxB['y2'] - boxB['y1'] + 1)
    return interArea / float(boxAArea + boxBArea - interArea)

def apply_nms(boxes, iou_thresh=0.5):
    boxes = sorted(boxes, key=lambda x: x['conf'], reverse=True)
    final = []
    while boxes:
        chosen = boxes.pop(0)
        boxes = [b for b in boxes if iou(chosen, b) < iou_thresh]
        final.append(chosen)
    return final

# 6. 시각화
def draw_final_boxes(image, boxes, class_names):
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
        crop = image[y1:y2, x1:x2]
        os.makedirs("cropped_notes", exist_ok=True)
        save_path = os.path.join("cropped_notes", f"note_{i+1}.png")
        cv2.imwrite(save_path, crop)
        cls = box['cls']
        conf = box['conf']
        label = f"{class_names[cls]} {conf:.2f}"
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(image, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return image