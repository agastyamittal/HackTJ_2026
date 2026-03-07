import numpy as np
import state
from config import TOP_K_SEARCH


def search(query_vec: np.ndarray, top_k: int = TOP_K_SEARCH, camera_ids: list[int] | None = None) -> list[dict]:
    candidates = []

    for upload_id, entry in state.uploads.items():
        if entry.get("status") != "done":
            continue
        if camera_ids and entry.get("camera_id") not in camera_ids:
            continue

        embeddings = entry["embeddings"]
        scores = (embeddings @ query_vec).tolist()

        for frame_idx, score in enumerate(scores):
            candidates.append({
                "upload_id": upload_id,
                "frame_idx": frame_idx,
                "score": float(score),
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]
