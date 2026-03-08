import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import state
from config import TOP_K_SEARCH, CAMERAS
from pipeline.embedder import encode_text
from pipeline.query_parser import parse_query
from utils.similarity import search as similarity_search

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = TOP_K_SEARCH
    camera_ids: list[int] | None = None


def _camera_info(camera_id: int) -> dict:
    for cam in CAMERAS:
        if cam["id"] == camera_id:
            return cam
    return {"id": camera_id, "name": f"Camera {camera_id}", "location": "", "lat": 0.0, "lon": 0.0}


def _score_cameras(query_features: list[str]) -> dict:
    """
    For each uploaded video, find the best single-entity match across all frames.
    A detection matches if its attributes cover the most queried features of any single entity.
    Score = max(matched_features / total_queried_features) over all detections in all frames.
    This prevents false positives from pooling attributes across different entities.
    """
    if not query_features:
        return {}

    feature_set = set(query_features)
    # camera_id -> (best_ratio, best_matched_set)
    camera_best: dict[int, tuple[float, set]] = {}

    for entry in state.uploads.values():
        if entry.get("status") != "done":
            continue
        cam_id = entry["camera_id"]

        for frame in entry.get("frames", []):
            for det in frame.get("detections", []):
                det_attrs = set()
                for attr in det.get("attributes", []):
                    name = attr["name"] if isinstance(attr, dict) else attr
                    det_attrs.add(name)

                matched = feature_set & det_attrs
                ratio = len(matched) / len(feature_set)

                if cam_id not in camera_best or ratio > camera_best[cam_id][0]:
                    camera_best[cam_id] = (ratio, matched)

    scores = {}
    for cam_id, (ratio, matched) in camera_best.items():
        status = "green" if ratio >= 0.8 else "yellow" if ratio >= 0.6 else "red"
        scores[str(cam_id)] = {
            "score":   round(ratio, 3),
            "matched": sorted(matched),
            "status":  status,
        }

    return scores


@router.post("")
def run_search(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(400, "Query cannot be empty")

    t0 = time.time()

    query_vec = encode_text(req.query)
    hits = similarity_search(query_vec, top_k=req.top_k, camera_ids=req.camera_ids)

    results = []
    for hit in hits:
        entry = state.uploads.get(hit["upload_id"])
        if not entry or hit["frame_idx"] >= len(entry["frames"]):
            continue

        frame = entry["frames"][hit["frame_idx"]]
        cam = _camera_info(entry["camera_id"])

        results.append({
            "upload_id":        hit["upload_id"],
            "frame_idx":        hit["frame_idx"],
            "camera_id":        entry["camera_id"],
            "camera_name":      entry["camera_name"],
            "camera_lat":       cam["lat"],
            "camera_lon":       cam["lon"],
            "timestamp_sec":    frame["timestamp_sec"],
            "similarity_score": round(hit["score"], 4),
            "thumbnail_url":    f"/api/frames/{hit['upload_id']}/{hit['frame_idx']}/thumbnail",
            "detections":       frame["detections"],
        })

    query_features = parse_query(req.query)
    camera_scores  = _score_cameras(query_features)

    query_time_ms = round((time.time() - t0) * 1000)
    return {
        "results":        results,
        "query_time_ms":  query_time_ms,
        "query":          req.query,
        "query_features": query_features,
        "camera_scores":  camera_scores,
    }
