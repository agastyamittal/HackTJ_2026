from pathlib import Path

BASE_DIR       = Path(__file__).parent
MODELS_DIR     = BASE_DIR / "models"
TEMP_DIR       = BASE_DIR / "data"
YOLO_WEIGHTS   = MODELS_DIR / "best.pt"

FRAME_INTERVAL  = 30
CLIP_MODEL      = "ViT-B/32"
CLIP_BATCH_SIZE = 32
YOLO_CONFIDENCE = 0.4
TOP_K_SEARCH    = 20

YOLO_BASE_CLASSES = [0, 2, 5, 7]  # 0=person, 2=car, 5=bus, 7=truck
CAMERAS = [
    {"id": 1, "name": "Super Chicken", "location": "Super Chicken", "lat": 38.920667667483485, "lon": -77.23499859339414, "status": "blue"},
    {"id": 2, "name": "Paris Baguette", "location": "Paris Baguette", "lat": 38.92307753179421, "lon": -77.23271941830107, "status": "blue"},
    {"id": 3, "name": "Booz-Allen Hamilton", "location": "Booz-Allen Hamilton", "lat": 38.92232109425155, "lon": -77.23160564103462, "status": "blue"},
    {"id": 4, "name": "Room 7101", "location": "Cvent HQ", "lat": 38.92209, "lon": -77.23325, "status": "blue"},
]

