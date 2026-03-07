import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import state
from config import TOP_K_SEARCH, CAMERAS
from pipeline.embedder import encode_text
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
            "upload_id":      hit["upload_id"],
            "frame_idx":      hit["frame_idx"],
            "camera_id":      entry["camera_id"],
            "camera_name":    entry["camera_name"],
            "camera_lat":     cam["lat"],
            "camera_lon":     cam["lon"],
            "timestamp_sec":  frame["timestamp_sec"],
            "similarity_score": round(hit["score"], 4),
            "thumbnail_url":  f"/api/frames/{hit['upload_id']}/{hit['frame_idx']}/thumbnail",
            "detections":     frame["detections"],
        })

    query_time_ms = round((time.time() - t0) * 1000)
    return {"results": results, "query_time_ms": query_time_ms, "query": req.query}
