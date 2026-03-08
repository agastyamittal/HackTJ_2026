"""
Attribute classifier inference wrappers.
Loaded once at startup; silently skipped if weight files don't exist.

person_attributes.pt  → classify_person(crop)  → list of active attribute strings
vehicle_attributes.pt → classify_vehicle(crop) → {"color": str, "type": str}
"""

from pathlib import Path
import numpy as np
import cv2
import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
from PIL import Image

from config import MODELS_DIR

PERSON_WEIGHTS  = MODELS_DIR / "person_attributes.pt"
VEHICLE_WEIGHTS = MODELS_DIR / "vehicle_attributes.pt"

_person_model   = None
_person_attrs   = None
_vehicle_model  = None
_vehicle_meta   = None   # {"color_names": [...], "type_names": [...]}

_device = "cuda" if torch.cuda.is_available() else "cpu"

_person_transform = transforms.Compose([
    transforms.Resize((256, 128)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

_vehicle_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


# ── Model definitions (must match training scripts) ────────────────────────────

def _build_person_model(num_attrs: int) -> nn.Module:
    """Build person model matching the training script structure (flat ResNet-18 keys)."""
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(512, num_attrs)
    return model


class _VehicleModel(nn.Module):
    def __init__(self, num_colors: int, num_types: int):
        super().__init__()
        backbone = models.resnet18(weights=None)
        self.features    = nn.Sequential(*list(backbone.children())[:-1])
        self.color_head  = nn.Linear(512, num_colors)
        self.type_head   = nn.Linear(512, num_types)

    def forward(self, x):
        f = self.features(x).flatten(1)
        return self.color_head(f), self.type_head(f)


# ── Public API ─────────────────────────────────────────────────────────────────

def load_classifiers() -> None:
    global _person_model, _person_attrs, _vehicle_model, _vehicle_meta

    if PERSON_WEIGHTS.exists():
        ckpt = torch.load(PERSON_WEIGHTS, map_location=_device)
        _person_attrs = ckpt["target_attrs"]
        model = _build_person_model(len(_person_attrs)).to(_device)
        model.load_state_dict(ckpt["model_state"])
        model.eval()
        _person_model = model
        print(f"[classifier] Loaded person attribute model ({len(_person_attrs)} attrs)")
    else:
        print("[classifier] person_attributes.pt not found — attribute classification disabled")

    if VEHICLE_WEIGHTS.exists():
        ckpt = torch.load(VEHICLE_WEIGHTS, map_location=_device)
        model = _VehicleModel(ckpt["num_colors"], ckpt["num_types"]).to(_device)
        model.load_state_dict(ckpt["model_state"])
        model.eval()
        _vehicle_model = model
        _vehicle_meta  = {
            "color_names": ckpt["color_names"],
            "type_names":  ckpt["type_names"],
        }
        print(f"[classifier] Loaded vehicle attribute model "
              f"({ckpt['num_colors']} colors, {ckpt['num_types']} types)")
    else:
        print("[classifier] vehicle_attributes.pt not found — vehicle attribute classification disabled")


# ── HSV color detection ────────────────────────────────────────────────────────

def _hsv_upper_color(crop: Image.Image) -> tuple[str, float] | None:
    """
    Detect dominant clothing color from the upper 60% of a person crop using HSV.
    Returns (attr_name, confidence) or None if no dominant color is found.
    Much more reliable than the ML model for basic colors.
    """
    try:
        w, h = crop.size
        upper = crop.crop((0, 0, w, int(h * 0.6))).convert("RGB")
        arr = np.array(upper, dtype=np.uint8)
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
        H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        total = float(H.size)

        masks = {
            "upperBodyBlack": (V < 55),
            "upperBodyWhite": (S < 40) & (V > 190),
            "upperBodyRed":   ((H < 12) | (H > 168)) & (S > 80) & (V > 60),
            "upperBodyBlue":  (H >= 100) & (H <= 135) & (S > 70) & (V > 50),
            "upperBodyGreen": (H >= 35) & (H <= 90) & (S > 70) & (V > 50),
        }

        counts = {name: float(mask.sum()) / total for name, mask in masks.items()}
        best_name = max(counts, key=counts.get)
        best_ratio = counts[best_name]

        if best_ratio >= 0.12:   # at least 12% of pixels match
            return best_name, round(min(best_ratio * 2.0, 0.98), 3)  # scale to ~confidence
    except Exception:
        pass
    return None


# Mutually exclusive attribute groups — pick only the top-confidence attr per group.
# Attributes not in any group are shown independently if above threshold.
_EXCLUSIVE_GROUPS = [
    ["upperBodyBlue", "upperBodyRed", "upperBodyBlack", "upperBodyWhite", "upperBodyGreen"],
    ["upperBodyLongSleeve", "upperBodyShortSleeve"],
    ["upperBodyCasual", "upperBodyFormal"],
    ["upperBodyTshirt", "upperBodyHoodie", "upperBodyJacket"],
    ["lowerBodyJeans", "lowerBodyTrousers", "lowerBodyShorts", "lowerBodySkirt"],
    ["personalMale", "personalFemale"],
    ["carryingBackpack", "carryingBag", "carryingMessengerBag", "carryingNothing"],
]
_MIN_GROUP_CONF = 0.35


_SUPPRESS_ATTRS = {"carryingNothing"}

def classify_person(crop: Image.Image) -> list[dict]:
    """
    Returns list of {"name": str, "confidence": float} for detected attributes.
    Uses exclusive-group logic: only the highest-confidence attr per group is returned.
    Returns [] if model not loaded.
    """
    if _person_model is None or _person_attrs is None:
        return []
    try:
        tensor = _person_transform(crop.convert("RGB")).unsqueeze(0).to(_device)
        with torch.no_grad():
            logits = _person_model(tensor)[0]
            probs  = torch.sigmoid(logits).cpu().numpy()

        attr_probs = dict(zip(_person_attrs, probs.tolist()))

        # Override color group with HSV detection (much more reliable for basic colors)
        hsv_result = _hsv_upper_color(crop)
        if hsv_result:
            hsv_attr, hsv_conf = hsv_result
            color_group = _EXCLUSIVE_GROUPS[0]  # upper body color group
            for attr in color_group:
                attr_probs[attr] = 0.05  # suppress all ML color predictions
            attr_probs[hsv_attr] = hsv_conf  # inject HSV winner

        result = []

        for group in _EXCLUSIVE_GROUPS:
            candidates = [(a, attr_probs[a]) for a in group if a in attr_probs]
            if not candidates:
                continue
            best_attr, best_conf = max(candidates, key=lambda x: x[1])
            if best_conf >= _MIN_GROUP_CONF and best_attr not in _SUPPRESS_ATTRS:
                result.append({"name": best_attr, "confidence": round(float(best_conf), 3)})

        return result
    except Exception as e:
        print(f"[classifier] classify_person error: {e}")
        return []


def classify_vehicle(crop: Image.Image) -> dict:
    """
    Returns {"color": str, "type": str, "color_conf": float, "type_conf": float}
    or {} if model not loaded.
    """
    if _vehicle_model is None or _vehicle_meta is None:
        return {}
    try:
        import torch.nn.functional as F
        tensor = _vehicle_transform(crop.convert("RGB")).unsqueeze(0).to(_device)
        with torch.no_grad():
            color_logits, type_logits = _vehicle_model(tensor)
        color_probs = F.softmax(color_logits, dim=1)[0]
        type_probs  = F.softmax(type_logits,  dim=1)[0]
        color_idx = int(color_probs.argmax().item())
        type_idx  = int(type_probs.argmax().item())
        return {
            "color":      _vehicle_meta["color_names"][color_idx],
            "type":       _vehicle_meta["type_names"][type_idx],
            "color_conf": round(float(color_probs[color_idx].item()), 3),
            "type_conf":  round(float(type_probs[type_idx].item()), 3),
        }
    except Exception as e:
        print(f"[classifier] classify_vehicle error: {e}")
        return {}
