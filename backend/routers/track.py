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


def _stable_attrs(entry: dict, source_class: str) -> set:
    """
    Build a stable attribute signature by voting across ALL frames in the source upload.
    Only returns attributes seen with conf >= 0.5 in >= 50% of detections of that class.
    This avoids using a single noisy frame as the person signature.
    """
    attr_counts: dict[str, int] = {}
    total_detections = 0

    for frame in entry.get("frames", []):
        for det in frame.get("detections", []):
            if det.get("class") != source_class:
                continue
            total_detections += 1
            for attr in det.get("attributes", []):
                name = attr["name"] if isinstance(attr, dict) else attr
                conf = attr.get("confidence", 1.0) if isinstance(attr, dict) else 1.0
                if conf >= 0.5:
                    attr_counts[name] = attr_counts.get(name, 0) + 1

    if total_detections == 0:
        return set()

    # Keep only attributes seen in > 50% of detections
    threshold = max(1, total_detections * 0.5)
    return {attr for attr, count in attr_counts.items() if count >= threshold}


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

    # CLIP embedding of source crop
    crop_embedding = encode_frames([crop])[0]

    # Stable attribute signature from source video (voting across all frames)
    source_class = det["class"]
    source_attrs = _stable_attrs(entry, source_class)

    other_upload_ids = [
        uid for uid, e in state.uploads.items()
        if uid != req.upload_id and e.get("status") == "done"
    ]
    if not other_upload_ids:
        return {"matches": [], "camera_scores": {}, "message": "No other cameras have processed footage"}

    other_camera_ids = list({state.uploads[uid]["camera_id"] for uid in other_upload_ids})
    hits = similarity_search(crop_embedding, top_k=30, camera_ids=other_camera_ids)

    matches = []
    for hit in hits:
        e = state.uploads.get(hit["upload_id"])
        if not e:
            continue
        f = e["frames"][hit["frame_idx"]]

        # Best single-entity attribute overlap in this hit frame
        attr_ratio = 0.0
        if source_attrs:
            for hit_det in f.get("detections", []):
                det_attrs = set()
                for attr in hit_det.get("attributes", []):
                    name = attr["name"] if isinstance(attr, dict) else attr
                    det_attrs.add(name)
                ratio = len(source_attrs & det_attrs) / len(source_attrs)
                if ratio > attr_ratio:
                    attr_ratio = ratio

        clip_score = hit["score"]
        combined = round(0.6 * clip_score + 0.4 * attr_ratio, 4)

        matches.append({
            "upload_id":       hit["upload_id"],
            "frame_idx":       hit["frame_idx"],
            "camera_id":       e["camera_id"],
            "camera_name":     e["camera_name"],
            "timestamp_sec":   f["timestamp_sec"],
            "clip_score":      round(clip_score, 4),
            "attribute_score": round(attr_ratio, 4),
            "combined_score":  combined,
            "thumbnail_url":   f"/api/frames/{hit['upload_id']}/{hit['frame_idx']}/thumbnail",
        })

    matches.sort(key=lambda x: x["combined_score"], reverse=True)

    # Per-camera summary for map markers
    camera_best: dict[int, dict] = {}
    for m in matches:
        cid = m["camera_id"]
        if cid not in camera_best or m["combined_score"] > camera_best[cid]["score"]:
            camera_best[cid] = {
                "score":              m["combined_score"],
                "best_timestamp_sec": m["timestamp_sec"],
                "best_upload_id":     m["upload_id"],
            }

    camera_scores = {}
    for cid, best in camera_best.items():
        s = best["score"]
        status = "green" if s >= 0.7 else "yellow" if s >= 0.5 else "red"
        camera_scores[str(cid)] = {
            "score":              round(s, 3),
            "status":             status,
            "best_timestamp_sec": best["best_timestamp_sec"],
            "best_upload_id":     best["best_upload_id"],
        }

    return {
        "matches":      matches[:20],
        "camera_scores": camera_scores,
        "source_class": source_class,
        "source_attrs": sorted(source_attrs),
    }
