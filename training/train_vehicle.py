"""
Train a dual-head vehicle attribute classifier on the VeRi dataset.
Predicts: color (10 classes) + type (9 classes)

Usage:
    cd training
    python train_vehicle.py

Output:
    ../backend/models/vehicle_attributes.pt
"""

from pathlib import Path
import torch
import torch.nn as nn
import torchvision.models as models
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

from dataset_veri import VeRiDataset

# ── Config ─────────────────────────────────────────────────────────────────────
BATCH_SIZE  = 32
EPOCHS      = 20
LR          = 1e-4
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
OUTPUT_PATH = Path(__file__).parent.parent / "backend" / "models" / "vehicle_attributes.pt"


class VehicleAttributeModel(nn.Module):
    def __init__(self, num_colors: int, num_types: int):
        super().__init__()
        backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.features = nn.Sequential(*list(backbone.children())[:-1])  # strip FC
        self.color_head = nn.Linear(512, num_colors)
        self.type_head  = nn.Linear(512, num_types)

    def forward(self, x):
        feats = self.features(x).flatten(1)
        return self.color_head(feats), self.type_head(feats)


def train_epoch(model, loader, color_crit, type_crit, optimizer):
    model.train()
    total_loss = 0.0
    for imgs, color_ids, type_ids in loader:
        imgs = imgs.to(DEVICE)
        color_ids, type_ids = color_ids.to(DEVICE), type_ids.to(DEVICE)
        optimizer.zero_grad()
        color_logits, type_logits = model(imgs)
        loss = color_crit(color_logits, color_ids) + type_crit(type_logits, type_ids)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * imgs.size(0)
    return total_loss / len(loader.dataset)


def val_epoch(model, loader, color_crit, type_crit):
    model.eval()
    total_loss, color_correct, type_correct, total = 0.0, 0, 0, 0
    with torch.no_grad():
        for imgs, color_ids, type_ids in loader:
            imgs = imgs.to(DEVICE)
            color_ids, type_ids = color_ids.to(DEVICE), type_ids.to(DEVICE)
            color_logits, type_logits = model(imgs)
            loss = color_crit(color_logits, color_ids) + type_crit(type_logits, type_ids)
            total_loss += loss.item() * imgs.size(0)
            color_correct += (color_logits.argmax(1) == color_ids).sum().item()
            type_correct  += (type_logits.argmax(1)  == type_ids).sum().item()
            total += imgs.size(0)
    return total_loss / len(loader.dataset), color_correct / total, type_correct / total


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"[train] Device: {DEVICE}")

    train_ds = VeRiDataset(train=True)
    val_ds   = VeRiDataset(train=False)

    if len(train_ds) == 0:
        print("[train] ERROR: No training samples found. Check DataSet/VeRi path.")
        return

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model      = VehicleAttributeModel(train_ds.num_colors, train_ds.num_types).to(DEVICE)
    color_crit = nn.CrossEntropyLoss()
    type_crit  = nn.CrossEntropyLoss()
    optimizer  = AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler  = CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_val_loss = float("inf")

    for epoch in range(1, EPOCHS + 1):
        train_loss = train_epoch(model, train_loader, color_crit, type_crit, optimizer)
        val_loss, color_acc, type_acc = val_epoch(model, val_loader, color_crit, type_crit)
        scheduler.step()

        print(f"Epoch {epoch:02d}/{EPOCHS}  "
              f"train_loss={train_loss:.4f}  val_loss={val_loss:.4f}  "
              f"color_acc={color_acc:.3f}  type_acc={type_acc:.3f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "model_state":  model.state_dict(),
                "num_colors":   train_ds.num_colors,
                "num_types":    train_ds.num_types,
                "color_names":  train_ds.color_names,
                "type_names":   train_ds.type_names,
            }, OUTPUT_PATH)
            print(f"  -> Saved best model to {OUTPUT_PATH}")

    print(f"\n[train] Done. Best val loss: {best_val_loss:.4f}")
    print(f"[train] Weights saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
