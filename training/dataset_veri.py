"""
PyTorch Dataset for the VeRi vehicle re-identification dataset.

Uses:
  - DataSet/VeRi/image_test/   (8,500 JPG vehicle crops)
  - DataSet/VeRi/test_label.xml  (colorID + typeID per image)
  - DataSet/VeRi/list_color.txt  (1-indexed color names)
  - DataSet/VeRi/list_type.txt   (1-indexed type names)
"""

from pathlib import Path
from io import BytesIO
import xml.etree.ElementTree as ET
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms


def _decode_file(path: Path) -> str:
    """Decode files stored as comma-separated ASCII decimal values."""
    raw = path.read_text(encoding="ascii", errors="ignore").strip()
    try:
        return "".join(chr(int(x)) for x in raw.split(","))
    except ValueError:
        return raw  # already plain text


def _load_image(img_path: Path) -> Image.Image:
    """Load an image that may be stored as comma-separated ASCII decimal values."""
    with open(img_path, "rb") as f:
        raw = f.read()
    # Real JPG starts with FF D8, real PNG with 89 50, real BMP with 42 4D
    if raw[:2] not in (b"\xff\xd8", b"\x89P", b"BM"):
        try:
            decoded = bytes(int(x) for x in raw.decode("ascii", errors="ignore").strip().split(","))
            return Image.open(BytesIO(decoded)).convert("RGB")
        except Exception:
            pass
    return Image.open(img_path).convert("RGB")

VERI_ROOT  = Path(__file__).parent.parent / "DataSet" / "VeRi"
IMAGE_DIR  = VERI_ROOT / "image_test"
LABEL_XML  = VERI_ROOT / "test_label.xml"
COLOR_LIST = VERI_ROOT / "list_color.txt"
TYPE_LIST  = VERI_ROOT / "list_type.txt"


def load_name_list(path: Path) -> list[str]:
    """Load a 1-indexed list file → returns 0-indexed list of names."""
    names = []
    for line in _decode_file(path).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        names.append(parts[-1].strip())
    return names


def parse_veri_labels(xml_path: Path) -> dict:
    """Returns {image_name: (color_id_0idx, type_id_0idx)}."""
    label_map = {}
    xml_str = _decode_file(xml_path)
    tree = ET.fromstring(xml_str)
    for item in tree.iter("Item"):
        img_name = item.get("imageName")
        color_id = item.get("colorID")
        type_id  = item.get("typeID")
        if img_name and color_id and type_id:
            label_map[img_name] = (int(color_id) - 1, int(type_id) - 1)
    return label_map


class VeRiDataset(Dataset):
    def __init__(self, train: bool = True, train_split: float = 0.85):
        self.color_names = load_name_list(COLOR_LIST)
        self.type_names  = load_name_list(TYPE_LIST)
        self.num_colors  = len(self.color_names)
        self.num_types   = len(self.type_names)

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip() if train else transforms.Lambda(lambda x: x),
            transforms.ColorJitter(brightness=0.2, contrast=0.2) if train else transforms.Lambda(lambda x: x),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

        label_map = parse_veri_labels(LABEL_XML)
        all_samples = []

        for img_path in sorted(IMAGE_DIR.glob("*.jpg")):
            key = img_path.name
            if key not in label_map:
                continue
            color_id, type_id = label_map[key]
            # Clamp to valid range
            color_id = max(0, min(color_id, self.num_colors - 1))
            type_id  = max(0, min(type_id,  self.num_types  - 1))
            all_samples.append((img_path, color_id, type_id))

        n_train = int(len(all_samples) * train_split)
        self.samples = all_samples[:n_train] if train else all_samples[n_train:]
        print(f"[VeRiDataset] {'Train' if train else 'Val'}: {len(self.samples)} samples  "
              f"({self.num_colors} colors, {self.num_types} types)")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, color_id, type_id = self.samples[idx]
        img = _load_image(img_path)
        img = self.transform(img)
        return img, torch.tensor(color_id, dtype=torch.long), torch.tensor(type_id, dtype=torch.long)
