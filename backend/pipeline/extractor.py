import cv2
from PIL import Image
from config import FRAME_INTERVAL


def extract_frames(filepath: str) -> tuple[list[dict], float, float]:
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video file: {filepath}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps

    frames = []
    frame_number = 0
    extracted_idx = 0

    while True:
        ret, bgr = cap.read()
        if not ret:
            break

        if frame_number % FRAME_INTERVAL == 0:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            if w > 640:
                scale = 640 / w
                rgb = cv2.resize(rgb, (640, int(h * scale)), interpolation=cv2.INTER_AREA)

            image = Image.fromarray(rgb)
            frames.append({
                "frame_idx": extracted_idx,
                "timestamp_sec": round(frame_number / fps, 3),
                "image": image,
            })
            extracted_idx += 1

        frame_number += 1

    cap.release()
    return frames, fps, duration_sec
