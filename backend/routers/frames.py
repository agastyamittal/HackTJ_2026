import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

import state

router = APIRouter(prefix="/api/frames", tags=["frames"])


@router.get("/{upload_id}/{frame_idx}/thumbnail")
def get_thumbnail(upload_id: str, frame_idx: int):
    entry = state.uploads.get(upload_id)
    if not entry:
        raise HTTPException(404, "Upload not found")
    frames = entry.get("frames", [])
    if frame_idx < 0 or frame_idx >= len(frames):
        raise HTTPException(404, "Frame not found")

    img = frames[frame_idx]["image"]
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/jpeg")


@router.get("/{upload_id}/{frame_idx}/detections")
def get_detections(upload_id: str, frame_idx: int):
    entry = state.uploads.get(upload_id)
    if not entry:
        raise HTTPException(404, "Upload not found")
    frames = entry.get("frames", [])
    if frame_idx < 0 or frame_idx >= len(frames):
        raise HTTPException(404, "Frame not found")

    frame = frames[frame_idx]
    return {
        "upload_id":     upload_id,
        "frame_idx":     frame_idx,
        "timestamp_sec": frame["timestamp_sec"],
        "detections":    frame["detections"],
    }


@router.get("/{upload_id}/all")
def get_all_frames(upload_id: str):
    entry = state.uploads.get(upload_id)
    if not entry:
        raise HTTPException(404, "Upload not found")
    if entry.get("status") != "done":
        raise HTTPException(202, "Video still processing")

    frames_summary = []
    for f in entry["frames"]:
        frames_summary.append({
            "frame_idx":        f["frame_idx"],
            "timestamp_sec":    f["timestamp_sec"],
            "detection_classes": list({d["class"] for d in f["detections"]}),
            "thumbnail_url":    f"/api/frames/{upload_id}/{f['frame_idx']}/thumbnail",
        })

    return {
        "upload_id":    upload_id,
        "camera_id":    entry["camera_id"],
        "camera_name":  entry["camera_name"],
        "duration_sec": entry.get("duration_sec"),
        "fps":          entry.get("fps"),
        "frames":       frames_summary,
    }
