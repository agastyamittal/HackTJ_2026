import io
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import state
from pipeline.embedder import encode_frames
from utils.similarity import search as similarity_search

router = APIRouter(prefix="/api/track", tags=["track"])


class TrackRequest(BaseModel):
    upload_id: str
    frame_idx: int
    detection_index: int   # index into frame.detections list


@router.post("")
def track_person(req: TrackRequest):
    entry = state.uploads.get(req.upload_id)
    if not entry or entry.get("status") != "done":
        raise HTTPException(404, "Upload not found or not ready")

    frames = entry.get("frames", [])
    if req.frame_idx >= len(frames):
        raise HTTPException(404, "Frame not found")

    frame = frames[req.frame_idx]
    detections = frame["detections"]
    if req.detection_index >= len(detections):
        raise HTTPException(404, "Detection index out of range")

    det = detections[req.detection_index]
    img = frame["image"]
    w, h = img.size
    x1n, y1n, x2n, y2n = det["bbox_norm"]

    x1, y1, x2, y2 = int(x1n * w), int(y1n * h), int(x2n * w), int(y2n * h)
    crop = img.crop((x1, y1, x2, y2))
    if crop.width < 10 or crop.height < 10:
        raise HTTPException(400, "Bounding box too small to track")

    crop_embedding = encode_frames([crop])[0]

    other_camera_ids = [
        e["camera_id"] for uid, e in state.uploads.items()
        if uid != req.upload_id and e.get("status") == "done"
    ]
    if not other_camera_ids:
        return {"matches": [], "message": "No other cameras have processed footage"}

    hits = similarity_search(crop_embedding, top_k=20, camera_ids=other_camera_ids)

    matches = []
    for hit in hits:
        e = state.uploads.get(hit["upload_id"])
        if not e:
            continue
        f = e["frames"][hit["frame_idx"]]
        matches.append({
            "upload_id":      hit["upload_id"],
            "frame_idx":      hit["frame_idx"],
            "camera_id":      e["camera_id"],
            "camera_name":    e["camera_name"],
            "timestamp_sec":  f["timestamp_sec"],
            "similarity_score": round(hit["score"], 4),
            "thumbnail_url":  f"/api/frames/{hit['upload_id']}/{hit['frame_idx']}/thumbnail",
        })

    return {"matches": matches, "source_class": det["class"]}
