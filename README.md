# MuseScore

**YOLO 기반 악보 인식 및 자동 MIDI 변환 프로젝트**

---

## 소개

MuseScore는 이미지 형태의 악보를 입력받아, YOLO 객체 탐지 모델을 활용해 음표와 쉼표, note head를 탐지하고 이를 기반으로 MIDI 형식의 음악 데이터로 자동 변환하는 딥러닝 기반 시스템입니다.

이 프로젝트는 다음과 같은 특징을 갖습니다:

* YOLOv11x으로 음표와 쉼표 객체 탐지
* YOLOv11m으로 note head만 정밀하게 탐지
* 오선 기준 pitch 추정 및 duration 계산
* pretty\_midi를 이용한 MIDI 자동 생성

---

---

## 설치 방법

```bash
git clone https://github.com/JReal2/MuseScan.git
cd MuseScan
pip install -r requirements.txt
```

필수 패키지:

* `ultralytics` (YOLOv8/v11)
* `pretty_midi`
* `opencv-python`
* `numpy`

---

## 사용 방법

### 1. note/rest 모델 학습

```bash
python scripts/train_note_yolo.py
```

### 2. head-only 모델 학습

```bash
python scripts/train_head_yolo.py
```

### 3. 추론 및 MIDI 변환

```bash
python scripts/infer_and_convert.py --image hush1.png --output output/melody.mid
```

---

## 예시 결과

* `debug_pitch_overlay.png`: 오선, note head, pitch 정보를 시각화한 이미지
* `output/melody.mid`: 추출된 MIDI 결과

---

## 주요 기능

| 기능           | 설명                          |
| ------------ | --------------------------- |
| 악보 이미지 입력    | 다양한 인쇄본 및 스캔본 지원            |
| note/rest 탐지 | YOLOv11n으로 객체 검출            |
| note head 탐지 | YOLOv8n 전용 모델로 중심 좌표 추출     |
| pitch 추정     | 오선 기준 상대 위치 + clef 구분       |
| MIDI 변환      | note pitch + duration 기반 생성 |

---

## 향후 개선 사항

* clef 기호 직접 인식
* 다성부 인식 및 velocity 표현 강화
* Web 앱 배포

