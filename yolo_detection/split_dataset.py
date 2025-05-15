# 이미지 분할

import os
import cv2
import shutil

def create_dirs(base_output_dir):
    for split in ['train', 'val']:
        os.makedirs(os.path.join(base_output_dir, 'images', split), exist_ok=True)
        os.makedirs(os.path.join(base_output_dir, 'labels', split), exist_ok=True)

def read_yolo_labels(label_path):
    labels = []
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            cls, x_c, y_c, w, h = map(float, parts)
            labels.append((int(cls), x_c, y_c, w, h))
    return labels

def convert_bbox(x_c, y_c, w, h, img_w, img_h):
    x1 = (x_c - w / 2) * img_w
    y1 = (y_c - h / 2) * img_h
    x2 = (x_c + w / 2) * img_w
    y2 = (y_c + h / 2) * img_h
    return x1, y1, x2, y2

def convert_bbox_back(x1, y1, x2, y2, patch_w, patch_h):
    x_c = ((x1 + x2) / 2) / patch_w
    y_c = ((y1 + y2) / 2) / patch_h
    w = (x2 - x1) / patch_w
    h = (y2 - y1) / patch_h
    return x_c, y_c, w, h

def split_image_and_labels(image, labels, img_path, output_img_dir, output_lbl_dir,
                           patch_size=(640, 640), stride=(480, 480)):
    h, w = image.shape[:2]
    patch_w, patch_h = patch_size
    stride_w, stride_h = stride

    patch_id = 0
    base_name = os.path.splitext(os.path.basename(img_path))[0]

    for y in range(0, h - patch_h + 1, stride_h):
        for x in range(0, w - patch_w + 1, stride_w):
            patch_img = image[y:y+patch_h, x:x+patch_w]
            patch_labels = []

            for cls, x_c, y_c, bw, bh in labels:
                x1, y1, x2, y2 = convert_bbox(x_c, y_c, bw, bh, w, h)
                # 중심이 패치 안에 있으면 포함
                if x <= x_c * w <= x + patch_w and y <= y_c * h <= y + patch_h:
                    # 박스 좌표를 패치 좌표계로 변환
                    new_x1 = max(x1 - x, 0)
                    new_y1 = max(y1 - y, 0)
                    new_x2 = min(x2 - x, patch_w)
                    new_y2 = min(y2 - y, patch_h)

                    # 너무 작으면 무시
                    if new_x2 - new_x1 < 5 or new_y2 - new_y1 < 5:
                        continue

                    new_xc, new_yc, new_w, new_h = convert_bbox_back(new_x1, new_y1, new_x2, new_y2, patch_w, patch_h)
                    patch_labels.append(f"{cls} {new_xc:.6f} {new_yc:.6f} {new_w:.6f} {new_h:.6f}")

            if patch_labels:
                patch_name = f"{base_name}_{patch_id:04}"
                cv2.imwrite(os.path.join(output_img_dir, f"{patch_name}.jpg"), patch_img)
                with open(os.path.join(output_lbl_dir, f"{patch_name}.txt"), 'w') as f:
                    f.write('\n'.join(patch_labels))
                patch_id += 1

def process_dataset_split(split, dataset_dir='dataset', output_dir='dataset_split',
                          patch_size=(640, 640), stride=(480, 480)):
    image_dir = os.path.join(dataset_dir, 'images', split)
    label_dir = os.path.join(dataset_dir, 'labels', split)

    output_img_dir = os.path.join(output_dir, 'images', split)
    output_lbl_dir = os.path.join(output_dir, 'labels', split)

    for fname in os.listdir(image_dir):
        if not fname.endswith('.jpg') and not fname.endswith('.png'):
            continue

        img_path = os.path.join(image_dir, fname)
        lbl_path = os.path.join(label_dir, os.path.splitext(fname)[0] + '.txt')

        image = cv2.imread(img_path)
        if not os.path.exists(lbl_path):
            continue

        labels = read_yolo_labels(lbl_path)
        split_image_and_labels(image, labels, img_path, output_img_dir, output_lbl_dir,
                               patch_size, stride)
        print(f"[INFO] Processed {fname}")

def run_all(dataset_dir='dataset', output_dir='dataset_split', patch_size=(640, 640), stride=(480, 480)):
    create_dirs(output_dir)
    for split in ['train', 'val']:
        print(f"\n[INFO] Processing {split} set...")
        process_dataset_split(split, dataset_dir, output_dir, patch_size, stride)
        shutil.copy(os.path.join(dataset_dir, 'data.yaml'), os.path.join(output_dir, 'data.yaml'))
    print("\n✅ 모든 이미지와 라벨이 분할 완료되었습니다.")

if __name__ == "__main__":
    run_all(
            dataset_dir='dataset',
            output_dir='dataset_split',
            patch_size=(640, 640),
            stride=(480, 480)
        )