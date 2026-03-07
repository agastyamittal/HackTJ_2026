import numpy as np
import torch
import clip
from config import CLIP_MODEL, CLIP_BATCH_SIZE

_model = None
_preprocess = None
_device = "cuda" if torch.cuda.is_available() else "cpu"


def load_model() -> None:
    global _model, _preprocess
    print(f"[embedder] Loading CLIP {CLIP_MODEL} on {_device}")
    _model, _preprocess = clip.load(CLIP_MODEL, device=_device)
    _model.eval()


def get_model():
    if _model is None:
        load_model()
    return _model, _preprocess


def encode_frames(images: list) -> np.ndarray:
    model, preprocess = get_model()
    all_embeddings = []

    for i in range(0, len(images), CLIP_BATCH_SIZE):
        batch = images[i : i + CLIP_BATCH_SIZE]
        tensors = torch.stack([preprocess(img) for img in batch]).to(_device)
        with torch.no_grad():
            feats = model.encode_image(tensors)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        all_embeddings.append(feats.cpu().numpy())

    return np.vstack(all_embeddings).astype(np.float32)


def encode_text(query: str) -> np.ndarray:
    model, _ = get_model()
    tokens = clip.tokenize([query]).to(_device)
    with torch.no_grad():
        feats = model.encode_text(tokens)
        feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats.cpu().numpy()[0].astype(np.float32)
