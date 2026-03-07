from pathlib import Path
from ultralytics import YOLO
from config import YOLO_WEIGHTS, YOLO_CONFIDENCE, YOLO_BASE_CLASSES

_model: YOLO | None = None
_using_custom: bool = False


def load_model() -> None:
    global _model, _using_custom
    if YOLO_WEIGHTS.exists():
        print(f"[detector] Loading custom YOLO weights: {YOLO_WEIGHTS}")
        _model = YOLO(str(YOLO_WEIGHTS))
        _using_custom = True
    else:
        print("[detector] Custom weights not found — using yolov8n.pt (COCO fallback)")
        _model = YOLO("yolov8n.pt")
        _using_custom = False


def get_model() -> YOLO:
    if _model is None:
        load_model()
    return _model


def detect(image) -> list[dict]:
    model = get_model()
    results = model(image, conf=YOLO_CONFIDENCE, verbose=False)[0]

    detections = []
    img_w, img_h = image.size

    for box in results.boxes:
        cls_id = int(box.cls[0])

        if not _using_custom and cls_id not in YOLO_BASE_CLASSES:
            continue

        cls_name = model.names[cls_id]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        detections.append({
            "class": cls_name,
            "confidence": round(confidence, 3),
            "bbox_norm": [
                round(x1 / img_w, 4),
                round(y1 / img_h, 4),
                round(x2 / img_w, 4),
                round(y2 / img_h, 4),
            ],
        })

    return detections
