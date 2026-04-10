import os
import cv2
import numpy as np

ENABLE_XCEPTION = os.getenv('ENABLE_XCEPTION', 'false').lower() == 'true'
MODEL_PATH = os.getenv('XCEPTION_MODEL_PATH', './ml/models/FF++_c23.pth')

_model = None


def load_xception_model():
    """
    Load pretrained XceptionNet model.
    Uses torchvision inception_v3 as the architecture base (compatible with FF++_c23.pth).
    Returns None if loading fails.
    """
    if not ENABLE_XCEPTION:
        return None
    try:
        import torch
        import torchvision.models as models

        model = models.inception_v3(pretrained=False, aux_logits=False)
        model.fc = torch.nn.Linear(model.fc.in_features, 2)
        checkpoint = torch.load(MODEL_PATH, map_location='cpu')
        model.load_state_dict(checkpoint, strict=False)
        model.eval()
        return model
    except Exception as e:
        print(f"[XceptionNet] Could not load model: {e}")
        return None


def check_xception(frames):
    """
    Signal 5 — XceptionNet Deep Learning (optional).
    Crops face regions, classifies real/fake via pretrained model.
    Only runs if ENABLE_XCEPTION=true and model file exists.
    Triggered if > 50% of face crops classified as fake.
    """
    global _model

    if not ENABLE_XCEPTION:
        return {
            "score": 0,
            "triggered": False,
            "available": False,
            "reason": "XceptionNet disabled — set ENABLE_XCEPTION=true and provide FF++_c23.pth to enable."
        }

    if _model is None:
        _model = load_xception_model()

    if _model is None:
        return {
            "score": 0,
            "triggered": False,
            "available": False,
            "reason": "XceptionNet model file not found. Download FF++_c23.pth and set XCEPTION_MODEL_PATH."
        }

    import torch
    import torchvision.transforms as transforms
    from PIL import Image

    transform = transforms.Compose([
        transforms.Resize((299, 299)),
        transforms.ToTensor(),
        transforms.Normalize([0.5] * 3, [0.5] * 3)
    ])

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    fake_votes = 0
    total_votes = 0

    for frame in frames[::3]:  # sample every 3rd frame for speed
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        for (x, y, w, h) in faces:
            face_crop = frame[y:y + h, x:x + w]
            pil_img = Image.fromarray(cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB))
            tensor = transform(pil_img).unsqueeze(0)
            with torch.no_grad():
                output = _model(tensor)
                pred = torch.argmax(output, dim=1).item()
                if pred == 1:
                    fake_votes += 1
                total_votes += 1

    if total_votes == 0:
        return {
            "score": 0,
            "triggered": False,
            "available": True,
            "reason": "No faces found for deep learning analysis."
        }

    fake_ratio = fake_votes / total_votes
    triggered = fake_ratio > 0.5

    return {
        "score": 25 if triggered else 0,
        "triggered": triggered,
        "available": True,
        "fake_ratio": round(fake_ratio, 3),
        "total_faces_analyzed": total_votes,
        "explanation": (
            f"Deep learning model flagged {fake_votes}/{total_votes} face crops as AI-generated."
            if triggered else
            f"Deep learning model found {fake_votes}/{total_votes} face crops suspicious — below threshold."
        )
    }
