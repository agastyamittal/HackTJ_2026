from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pipeline.detector import load_model as load_yolo
from pipeline.embedder import load_model as load_clip
from pipeline.classifier import load_classifiers
from routers import cameras, videos, search, frames, stream, track


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] Loading YOLO model...")
    load_yolo()
    print("[startup] Loading CLIP model...")
    load_clip()
    print("[startup] Loading attribute classifiers...")
    load_classifiers()
    print("[startup] Models ready. Argus is running.")
    yield
    print("[shutdown] Shutting down.")


app = FastAPI(title="Argus", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router)
app.include_router(videos.router)
app.include_router(search.router)
app.include_router(frames.router)
app.include_router(stream.router)
app.include_router(track.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Sentinal"}
