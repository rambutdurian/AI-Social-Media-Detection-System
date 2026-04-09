# backend/analyzers/detector.py
import sys, cv2, torch
import numpy as np
import torch.nn as nn
from torchvision import transforms
from pathlib import Path


# Clone once: cd backend/analyzers && git clone https://github.com/HongguLiu/Deepfake-Detection.git DeepfakeDetection
REPO_PATH = Path(__file__).parent / "DeepfakeDetection"
if str(REPO_PATH) not in sys.path:
    sys.path.insert(0, str(REPO_PATH))

try:
    from network.models import model_selection  # from HongguLiu repo
except ImportError:
    raise RuntimeError(
        "Deepfake-Detection repo not found. Run:\n"
        "cd backend/analyzers && git clone https://github.com/HongguLiu/Deepfake-Detection.git DeepfakeDetection"
    )

WEIGHTS_PATH = r"C:\Users\qistina\Documents\AI hackathon\FaceForensics++ pretrained models\FF++_c23.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_model = None


def _load_model():
    """Loads the XceptionNet model once and caches it (singleton pattern)."""
    global _model
    if _model is not None:
        return _model
    model, *_ = model_selection(modelname="xception", num_out_classes=2)
    state = torch.load(WEIGHTS_PATH, map_location=DEVICE)
    state = state.get("model", state.get("state_dict", state))
    model.load_state_dict(state, strict=False)
    model.to(DEVICE)
    model.eval()
    _model = model
    return _model


TRANSFORM = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((299, 299)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])


def analyze_frame(cv2_frame) -> float:
    """
    Input:  OpenCV BGR frame (numpy ndarray)
    Output: float in [0.0, 1.0] — probability the frame is a deepfake
    """
    model = _load_model()
    rgb = cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2RGB)
    tensor = TRANSFORM(rgb).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        logits = model(tensor)
        prob = torch.softmax(logits, dim=1)[0][1].item()  # index 1 = fake class
    return round(prob, 4)
