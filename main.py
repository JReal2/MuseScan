from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.responses import FileResponse
import subprocess
import os, sys
import cv2
import numpy as np
from tempfile import NamedTemporaryFile
from ultralytics import YOLO
from yolo_detection.data_preprocess import (
    remove_staff_lines,
    split_image_with_offsets,
    run_yolo_on_patches,
    restore_to_original_coords,
    apply_nms,
    draw_final_boxes
)
from yolo_detection.midi_extract import convert_boxes_to_midi_from_heads
from midi2audio import FluidSynth
from pydub import AudioSegment

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 ["http://localhost:3000"] 등으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.environ["PATH"] += os.pathsep + "E:/Downloads/fluidsynth-2.4.6-win10-x64/bin"

# 모델 및 사운드폰트 경로
MODEL_PATH = "best/x_best.pt"
SOUNDFONT_PATH = "FluidR3_GM.sf2"

model = YOLO(MODEL_PATH)
class_names = model.names
TMP_WAV = "temp.wav"

# MIDI → MP3 변환 함수
def midi_to_mp3(midi_path, mp3_path):
    if not os.path.exists(SOUNDFONT_PATH):
        raise FileNotFoundError(f"SoundFont not found: {SOUNDFONT_PATH}")
    if not os.path.exists(midi_path):
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    # fluidsynth 명령어 직접 실행
    cmd = [
        "fluidsynth",
        "-ni",
        "-F", TMP_WAV,
        "-r", "44100",
        SOUNDFONT_PATH,
        midi_path
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"fluidsynth execution failed: {e}")

    if not os.path.exists(TMP_WAV):
        raise RuntimeError("WAV file not created. fluidsynth failed silently.")

    # pydub로 mp3 인코딩
    audio = AudioSegment.from_wav(TMP_WAV)
    audio.export(mp3_path, format="mp3")

    os.remove(TMP_WAV)

# 이미지 처리 → MIDI 및 MP3 생성
def process_image_and_generate_audio(image_bytes: bytes, filename: str):
    with NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        tmp_file.write(image_bytes)
        tmp_path = tmp_file.name

    image = cv2.imread(tmp_path)
    cleaned = remove_staff_lines(image)

    patch_size = (640, 640)
    stride = (480, 480)
    patches, positions = split_image_with_offsets(cleaned, patch_size, stride)

    results = run_yolo_on_patches(model, patches, conf=0.25)
    restored = restore_to_original_coords(results, positions, patch_size)
    merged_boxes = apply_nms(restored, iou_thresh=0.5)

    result_img_path = f"sample_detected/{filename}_detected.png"
    os.makedirs(os.path.dirname(result_img_path), exist_ok=True)
    cv2.imwrite(result_img_path, draw_final_boxes(image.copy(), merged_boxes, class_names))

    output_midi = f"sample_detected/{filename}.mid"
    convert_boxes_to_midi_from_heads(merged_boxes, image, output_midi)

    output_mp3 = f"sample_detected/{filename}.mp3"
    midi_to_mp3(output_midi, output_mp3)

    return result_img_path, output_midi, output_mp3

# 업로드 API
@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    print(f"[✅] Received file: {file.filename}")

    contents = await file.read()
    filename = os.path.splitext(file.filename)[0]

    try:
        result_img, midi_path, mp3_path = process_image_and_generate_audio(contents, filename)
        print(f"[🎯] Files saved:")
        print(f"    ➤ Result image : {result_img}")
        print(f"    ➤ MIDI         : {midi_path}")
        print(f"    ➤ MP3          : {mp3_path}")
        
        return {
            "midi_file": f"/download/{os.path.basename(midi_path)}",
            "mp3_file": f"/download/{os.path.basename(mp3_path)}",
            "preview_image": f"/download/{os.path.basename(result_img)}"
        }
    except Exception as e:
        print(f"[❌] Upload processing error: {e}")
        return {"error": str(e)}


# 파일 다운로드 엔드포인트
@app.get("/download/{filename}")
def download_file(filename: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "sample_detected", filename)
    
    print(f"[📥] Download requested: {filename}")
    print(f"[🧭] Resolved path: {file_path}")

    if not os.path.exists(file_path):
        print("[❌] File not found")
        raise HTTPException(status_code=404, detail="File not found")
    
    print("[✅] File exists, sending response.")
    
    media_type = "application/octet-stream"
    if filename.endswith(".mp3"):
        media_type = "audio/mpeg"
    elif filename.endswith(".mid"):
        media_type = "audio/midi"
    elif filename.endswith(".png"):
        media_type = "image/png"

    return FileResponse(file_path, media_type=media_type, filename=filename)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
