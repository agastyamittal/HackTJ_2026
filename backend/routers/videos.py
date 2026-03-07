import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException

import state
from config import TEMP_DIR, CAMERAS
from pipeline.processor import process_video

router = APIRouter(prefix="/api/videos", tags=["videos"])

TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _camera_name(camera_id: int) -> str:
    for cam in CAMERAS:
        if cam["id"] == camera_id:
            return cam["name"]
    return f"Camera {camera_id}"


@router.post("")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    camera_id: int = Form(...),
):
    upload_id = str(uuid.uuid4())
    dest = TEMP_DIR / f"{upload_id}_{file.filename}"

    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    state.uploads[upload_id] = {
        "camera_id":   camera_id,
        "camera_name": _camera_name(camera_id),
        "filepath":    str(dest),
        "filename":    file.filename,
        "status":      "pending",
        "error_msg":   None,
        "fps":         None,
        "duration_sec": None,
        "frames":      [],
        "embeddings":  None,
    }

    background_tasks.add_task(process_video, upload_id, str(dest), camera_id)

    return {"upload_id": upload_id, "status": "processing"}


@router.get("/{upload_id}/status")
def get_status(upload_id: str):
    entry = state.uploads.get(upload_id)
    if not entry:
        raise HTTPException(404, "Upload not found")
    return {
        "upload_id":   upload_id,
        "status":      entry["status"],
        "frame_count": len(entry.get("frames", [])),
        "duration_sec": entry.get("duration_sec"),
        "error_msg":   entry.get("error_msg"),
    }


@router.get("")
def list_uploads():
    result = []
    for upload_id, entry in state.uploads.items():
        result.append({
            "upload_id":   upload_id,
            "camera_id":   entry["camera_id"],
            "camera_name": entry["camera_name"],
            "filename":    entry.get("filename"),
            "status":      entry["status"],
            "frame_count": len(entry.get("frames", [])),
            "duration_sec": entry.get("duration_sec"),
        })
    return result
