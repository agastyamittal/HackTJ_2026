"""
Train a multi-label person attribute classifier on the PETA dataset.

Usage:
    cd training
    python train_attributes.py

Output:
    ../backend/models/person_attributes.pt
"""

from pathlib import Path
import torch
import torch.nn as nn
import torchvision.models as models
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

from dataset_peta import PETADataset, NUM_ATTRS, TARGET_ATTRS

# ── Config ─────────────────────────────────────────────────────────────────────
BATCH_SIZE  = 32
EPOCHS      = 40
LR          = 1e-4
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
OUTPUT_PATH = Path(__file__).parent.parent / "backend" / "models" / "person_attributes.pt"


def build_model():
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = nn.Linear(512, NUM_ATTRS)
    return model


def train_epoch(model, loader, criterion, optimizer):
    model.train()
    total_loss = 0.0
    for imgs, labels in loader:
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        logits = model(imgs)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * imgs.size(0)
    return total_loss / len(loader.dataset)


def val_epoch(model, loader, criterion):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for imgs, labels in loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            logits = model(imgs)
            loss = criterion(logits, labels)
            total_loss += loss.item() * imgs.size(0)
            preds = (torch.sigmoid(logits) > 0.5).float()
            correct += (preds == labels).all(dim=1).sum().item()
            total += imgs.size(0)
    return total_loss / len(loader.dataset), correct / total


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"[train] Device: {DEVICE}")

    train_ds = PETADataset(train=True)
    val_ds   = PETADataset(train=False)

    if len(train_ds) == 0:
        print("[train] ERROR: No training samples found. Check DataSet/PETA path.")
        return

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model = build_model().to(DEVICE)

    # Compute per-attribute pos_weight to handle class imbalance
    all_labels = torch.stack([train_ds[i][1] for i in range(len(train_ds))])
    pos_counts = all_labels.sum(dim=0).clamp(min=1.0)
    neg_counts = len(train_ds) - pos_counts
    pos_weight = (neg_counts / pos_counts).to(DEVICE)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    optimizer = AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_val_loss = float("inf")

    for epoch in range(1, EPOCHS + 1):
        train_loss = train_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc = val_epoch(model, val_loader, criterion)
        scheduler.step()

        print(f"Epoch {epoch:02d}/{EPOCHS}  "
              f"train_loss={train_loss:.4f}  "
              f"val_loss={val_loss:.4f}  "
              f"val_exact_acc={val_acc:.3f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "model_state": model.state_dict(),
                "target_attrs": TARGET_ATTRS,
                "num_attrs": NUM_ATTRS,
            }, OUTPUT_PATH)
            print(f"  -> Saved best model to {OUTPUT_PATH}")

    print(f"\n[train] Done. Best val loss: {best_val_loss:.4f}")
    print(f"[train] Weights saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
