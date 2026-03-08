"""
PyTorch Dataset for the PETA pedestrian attribute dataset.

Covers all three subsets:
  - PETA dataset/3DPeS/archive/
  - PETA dataset/TownCentre/archive/
  - PETA dataset/i-LID/archive/

Each subset has:
  - BMP images named  {id}_{seq}_FRAME_{n}_RGB.bmp
  - Label.txt with rows:  {id} attr1 attr2 ...
"""

from pathlib import Path
from io import BytesIO
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms

# ── Attributes we actually care about (22 demo-relevant labels) ────────────────
TARGET_ATTRS = [
    "upperBodyBlue", "upperBodyRed", "upperBodyBlack",
    "upperBodyWhite", "upperBodyGreen",
    "upperBodyLongSleeve", "upperBodyShortSleeve",
    "upperBodyCasual", "upperBodyFormal",
    "upperBodyTshirt", "upperBodyHoodie", "upperBodyJacket",
    "lowerBodyJeans", "lowerBodyTrousers", "lowerBodyShorts", "lowerBodySkirt",
    "carryingBackpack", "carryingBag", "carryingMessengerBag", "carryingNothing",
    "personalMale", "personalFemale",
]

NUM_ATTRS = len(TARGET_ATTRS)
ATTR_TO_IDX = {a: i for i, a in enumerate(TARGET_ATTRS)}

# ── Dataset root (relative to this file) ──────────────────────────────────────
PETA_ROOT = Path(__file__).parent.parent / "DataSet" / "PETA" / "PETA dataset"

SUBSETS = [
    PETA_ROOT / "3DPeS"      / "archive",
    PETA_ROOT / "TownCentre" / "archive",
    PETA_ROOT / "i-LID"      / "archive",
]


def parse_label_file(label_path: Path) -> dict:
    """Returns {pedestrian_id (int): set of active attribute strings}.

    Handles two formats:
    1. Normal text: '1 upperBodyBlue lowerBodyBlack ...'
    2. Comma-separated ASCII decimals: '49,32,117,112,...' (each char encoded as its ASCII value)
    """
    label_map = {}
    with open(label_path, "r") as f:
        raw = f.read().strip()

    # Detect comma-separated ASCII decimal encoding
    first_token = raw.split(",")[0].strip()
    if first_token.isdigit() and int(first_token) < 256 and "," in raw[:20]:
        try:
            raw = "".join(chr(int(x)) for x in raw.split(","))
        except ValueError:
            pass  # fall through to normal parsing

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        label_map[pid] = set(parts[1:])
    return label_map


def _load_image(img_path: Path) -> Image.Image:
    """Load a BMP image that may be stored as comma-separated ASCII decimal values."""
    with open(img_path, "rb") as f:
        raw = f.read()
    # If the file starts with printable ASCII digits/commas, it's the encoded format
    if raw[:2] not in (b"BM", b"\xff\xd8"):  # not real BMP or JPEG header
        try:
            decoded = bytes(int(x) for x in raw.decode("ascii").strip().split(","))
            return Image.open(BytesIO(decoded)).convert("RGB")
        except Exception:
            pass
    return Image.open(img_path).convert("RGB")


class PETADataset(Dataset):
    def __init__(self, train: bool = True, train_split: float = 0.85):
        self.samples = []   # list of (image_path, label_vector)
        if train:
            self.transform = transforms.Compose([
                transforms.Resize((256, 128)),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(degrees=8),
                transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.2, hue=0.05),
                transforms.ToTensor(),
                transforms.RandomErasing(p=0.3, scale=(0.02, 0.15)),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225]),
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize((256, 128)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225]),
            ])

        all_samples = []
        for subset_dir in SUBSETS:
            label_file = subset_dir / "Label.txt"
            if not label_file.exists():
                print(f"[PETADataset] WARNING: Label.txt not found in {subset_dir}")
                continue

            label_map = parse_label_file(label_file)

            for img_path in sorted(subset_dir.glob("*.bmp")):
                try:
                    pid = int(img_path.name.split("_")[0])
                except ValueError:
                    continue

                if pid not in label_map:
                    continue

                attrs = label_map[pid]
                label_vec = torch.zeros(NUM_ATTRS, dtype=torch.float32)
                for attr in attrs:
                    if attr in ATTR_TO_IDX:
                        label_vec[ATTR_TO_IDX[attr]] = 1.0

                try:
                    _load_image(img_path)  # validate readable
                    all_samples.append((img_path, label_vec))
                except Exception:
                    pass  # skip corrupt/unreadable images

        # Train / val split (deterministic)
        n_train = int(len(all_samples) * train_split)
        if train:
            self.samples = all_samples[:n_train]
        else:
            self.samples = all_samples[n_train:]

        print(f"[PETADataset] {'Train' if train else 'Val'}: {len(self.samples)} samples")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label_vec = self.samples[idx]
        img = _load_image(img_path)
        img = self.transform(img)
        return img, label_vec
