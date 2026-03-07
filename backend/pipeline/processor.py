import state
from pipeline.extractor import extract_frames
from pipeline.detector import detect
from pipeline.embedder import encode_frames
from config import CAMERAS


def _camera_name(camera_id: int) -> str:
    for cam in CAMERAS:
        if cam["id"] == camera_id:
            return cam["name"]
    return f"Camera {camera_id}"


def process_video(upload_id: str, filepath: str, camera_id: int) -> None:
    entry = state.uploads[upload_id]
    entry["status"] = "processing"

    try:
        print(f"[processor:{upload_id}] Extracting frames from {filepath}")
        raw_frames, fps, duration_sec = extract_frames(filepath)
        entry["fps"] = fps
        entry["duration_sec"] = duration_sec
        print(f"[processor:{upload_id}] Extracted {len(raw_frames)} frames  ({duration_sec:.1f}s @ {fps}fps)")

        print(f"[processor:{upload_id}] Running YOLO detection...")
        processed_frames = []
        for f in raw_frames:
            detections = detect(f["image"])
            processed_frames.append({
                "frame_idx":     f["frame_idx"],
                "timestamp_sec": f["timestamp_sec"],
                "image":         f["image"],
                "detections":    detections,
            })

        print(f"[processor:{upload_id}] Encoding {len(processed_frames)} frames with CLIP...")
        pil_images = [f["image"] for f in processed_frames]
        embeddings = encode_frames(pil_images)

        entry["frames"]     = processed_frames
        entry["embeddings"] = embeddings
        entry["status"]     = "done"
        print(f"[processor:{upload_id}] Done. {len(processed_frames)} frames indexed.")

    except Exception as exc:
        entry["status"]    = "error"
        entry["error_msg"] = str(exc)
        print(f"[processor:{upload_id}] ERROR: {exc}")
        raise
