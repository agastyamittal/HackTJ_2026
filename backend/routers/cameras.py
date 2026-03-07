from fastapi import APIRouter
from config import CAMERAS

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.get("")
def list_cameras():
    return CAMERAS
