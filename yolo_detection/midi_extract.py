import cv2
import numpy as np
import pretty_midi
from ultralytics import YOLO

# ------------------------
# 상수 정의
# ------------------------
CLASS_NAMES = [
    'eighth_note', 'eighth_rest', 'half_note', 'half_rest',
    'quarter_note', 'quarter_rest', 'sixteenth_note',
    'whole_note', 'whole_rest'
]

NOTE_DURATION = {
    'whole_note': 2.0,
    'half_note': 1.0,
    'quarter_note': 0.5,
    'eighth_note': 0.25,
    'sixteenth_note': 0.125,
}

REST_CLASSES = {'whole_rest', 'half_rest', 'quarter_rest', 'eighth_rest'}

G_CLEF_PITCHES = [
    'A5', 'G5', 'F5', 'E5', 'D5', 'C5', 'B4', 'A4',
    'G4', 'F4', 'E4', 'D4', 'C4', 'B3', 'A3'
]

F_CLEF_PITCHES = [
    'C4', 'B3', 'A3', 'G3', 'F3', 'E3', 'D3', 'C3',
    'B2', 'A2', 'G2', 'F2', 'E2', 'D2', 'C2'
]

# ------------------------
# 오선 검출 및 군집화
# ------------------------
def detect_staff_lines_from_removal(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (image.shape[1] // 15, 1))
    lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    y_positions = [y for y in range(lines.shape[0]) if np.count_nonzero(lines[y, :]) > 0.5 * lines.shape[1]]
    return sorted(set(y_positions))

def cluster_staff_lines(y_positions, group_size=5, threshold=12):
    blocks, current = [], [y_positions[0]]
    for y in y_positions[1:]:
        if abs(y - current[-1]) <= threshold:
            current.append(y)
        else:
            if len(current) >= group_size:
                blocks.append(current[:group_size])
            current = [y]
    if len(current) >= group_size:
        blocks.append(current[:group_size])
    return blocks

def find_nearest_staff_block(y_center, staff_blocks):
    return min(staff_blocks, key=lambda b: abs(np.mean(b) - y_center))

def is_upper_staff(staff_block, image_height):
    return np.mean(staff_block) < image_height / 2

# ------------------------
# note head 추정
# ------------------------
def find_note_head_within_box(image, box, head_model):
    x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(image.shape[1], x2), min(image.shape[0], y2)
    crop = image[y1:y2, x1:x2]

    result = head_model.predict(source=crop, conf=0.01, verbose=False)[0]
    if not result.boxes or len(result.boxes) == 0:
        print(f"[⚠️ Head 예측 실패] box: ({x1},{y1},{x2},{y2})")
        cv2.imwrite(f'debug_failed_crop_{x1}_{y1}.png', crop)
        return None

    head_box = result.boxes[0]
    hx1, hy1, hx2, hy2 = map(int, head_box.xyxy[0])
    y_center = int((hy1 + hy2) / 2)

    debug_crop = crop.copy()
    cv2.rectangle(debug_crop, (hx1, hy1), (hx2, hy2), (0, 255, 255), 2)
    cv2.line(debug_crop, (0, y_center), (debug_crop.shape[1], y_center), (0, 0, 255), 1)
    # cv2.imwrite(f'debug_crop_head_{x1}_{y1}.png', debug_crop)

    return y_center + y1  # 원본 이미지 기준

# ------------------------
# pitch 추정
# ------------------------
def estimate_pitch(y, staff_block, clef):
    lines = sorted(staff_block)
    spacing = np.mean(np.diff(lines))
    base_y = lines[-1]  # 아래줄 기준
    idx = int(round((base_y - y) / (spacing / 2)))
    table = G_CLEF_PITCHES if clef == 'G' else F_CLEF_PITCHES
    return table[max(0, min(idx, len(table) - 1))]


def note_name_to_midi(note_str):
    try:
        return pretty_midi.note_name_to_number(note_str)
    except:
        return 60

# ------------------------
# MIDI 변환
# ------------------------
def convert_boxes_to_midi_from_heads(boxes, image, output_path):
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    image_height = image.shape[0]
    y_positions = detect_staff_lines_from_removal(image)
    staff_blocks = cluster_staff_lines(y_positions)

    debug_img = image.copy()
    for y in sum(staff_blocks, []):
        cv2.line(debug_img, (0, y), (debug_img.shape[1], y), (200, 200, 0), 1)

    notes = []
    pitch_names = []
    head_y_list = []
    head_model = YOLO('best/best_head.pt')

    for box in boxes:
        cls_idx = int(box['cls'])
        cls_name = CLASS_NAMES[cls_idx]
        if cls_name in REST_CLASSES or cls_name not in NOTE_DURATION:
            continue

        head_y = find_note_head_within_box(image, box, head_model)
        if head_y is None:
            continue

        staff_block = find_nearest_staff_block(head_y, staff_blocks)
        clef = 'G' if is_upper_staff(staff_block, image_height) else 'F'
        pitch_name = estimate_pitch(head_y, staff_block, clef)
        midi_pitch = note_name_to_midi(pitch_name)
        duration = NOTE_DURATION[cls_name]

        x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
        x_center = int((x1 + x2) / 2)
        notes.append((x_center, midi_pitch, duration))
        pitch_names.append(f"{pitch_name}({clef})")
        head_y_list.append(head_y)

    for box, pitch, head_y in zip(boxes, pitch_names, head_y_list):
        x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
        x_center = int((x1 + x2) / 2)
        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 1)
        cv2.circle(debug_img, (x_center, head_y), 3, (0, 0, 255), -1)
        cv2.putText(debug_img, pitch, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    cv2.imwrite("debug_pitch_overlay.png", debug_img)

    notes.sort(key=lambda x: x[0])
    time = 0.0
    for _, pitch, dur in notes:
        instrument.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=time, end=time + dur))
        time += dur

    midi.instruments.append(instrument)
    midi.write(output_path)
    print(f"[🎵 MIDI 저장 완료] → {output_path}")
