from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

import state

router = APIRouter(prefix="/api/video", tags=["stream"])


@router.get("/{upload_id}/clip")
def stream_video(upload_id: str):
    entry = state.uploads.get(upload_id)
    if not entry:
        raise HTTPException(404, "Upload not found")

    filepath = Path(entry["filepath"])
    if not filepath.exists():
        raise HTTPException(404, "Video file not found on disk")

    return FileResponse(
        path=str(filepath),
        media_type="video/mp4",
        filename=entry.get("filename", "video.mp4"),
    )
