from pathlib import Path
from ultralytics import YOLO
from config import YOLO_WEIGHTS, YOLO_CONFIDENCE, YOLO_BASE_CLASSES
from pipeline.classifier import classify_person, classify_vehicle
from pipeline.query_parser import VEHICLE_COLOR_TO_TOKEN, VEHICLE_TYPE_TO_TOKEN

_VEHICLE_CLASSES = {"car", "bus", "truck"}

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

        det = {
            "class": cls_name,
            "confidence": round(confidence, 3),
            "bbox_norm": [
                round(x1 / img_w, 4),
                round(y1 / img_h, 4),
                round(x2 / img_w, 4),
                round(y2 / img_h, 4),
            ],
            "attributes": [],
        }

        # Crop and run attribute classifier
        x1i, y1i, x2i, y2i = int(x1), int(y1), int(x2), int(y2)
        if x2i > x1i and y2i > y1i:
            crop = image.crop((x1i, y1i, x2i, y2i))
            if cls_name == "person":
                det["attributes"] = classify_person(crop)
            elif cls_name in _VEHICLE_CLASSES:
                vehicle_attrs = classify_vehicle(crop)
                if vehicle_attrs:
                    color_token = VEHICLE_COLOR_TO_TOKEN.get(vehicle_attrs.get("color", ""))
                    type_token  = VEHICLE_TYPE_TO_TOKEN.get(vehicle_attrs.get("type", ""))
                    det["attributes"] = [
                        a for a in [
                            {"name": color_token, "confidence": vehicle_attrs["color_conf"]} if color_token else None,
                            {"name": type_token,  "confidence": vehicle_attrs["type_conf"]}  if type_token  else None,
                        ] if a is not None
                    ]

        detections.append(det)

    return detections
