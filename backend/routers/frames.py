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

from pydantic import BaseModel


class QueryMatchRequest(BaseModel):
    query_features: list[str]


@router.post("/{upload_id}/query_matches")
def query_matches(upload_id: str, req: QueryMatchRequest):
    """
    For each frame, find the best single-entity match ratio against query features.
    Returns frames where at least one detection partially matches,
    colored green/yellow/red by match ratio.
    """
    entry = state.uploads.get(upload_id)
    if not entry or entry.get("status") != "done":
        raise HTTPException(404, "Upload not found or not done")

    feature_set = set(req.query_features)
    if not feature_set:
        return []

    results = []
    for frame in entry.get("frames", []):
        best_ratio = 0.0
        best_matched: set = set()
        for det in frame.get("detections", []):
            det_attrs = set()
            for attr in det.get("attributes", []):
                name = attr["name"] if isinstance(attr, dict) else attr
                det_attrs.add(name)
            matched = feature_set & det_attrs
            ratio = len(matched) / len(feature_set)
            if ratio > best_ratio:
                best_ratio = ratio
                best_matched = matched

        if best_ratio > 0:
            status = "green" if best_ratio >= 0.8 else "yellow" if best_ratio >= 0.6 else "red"
            results.append({
                "frame_idx":     frame["frame_idx"],
                "timestamp_sec": frame["timestamp_sec"],
                "best_ratio":    round(best_ratio, 3),
                "status":        status,
                "matched":       sorted(best_matched),
            })

    return results
