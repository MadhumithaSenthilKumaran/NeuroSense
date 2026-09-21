"""Compatibility wrapper for legacy and Tasks-only MediaPipe wheels."""

from pathlib import Path
from types import SimpleNamespace
from urllib.request import urlretrieve

import mediapipe as mp


MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "hand_landmarker.task"


def create_hands():
    if hasattr(mp, "solutions"):
        return mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75
        )
    if not MODEL_PATH.exists():
        MODEL_PATH.parent.mkdir(exist_ok=True)
        urlretrieve(MODEL_URL, MODEL_PATH)
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.75,
        min_hand_presence_confidence=0.75,
        min_tracking_confidence=0.75,
    )
    return _TasksHands(options)


class _TasksHands:
    def __init__(self, options):
        from mediapipe.tasks.python import vision
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._timestamp_ms = 0

    def process(self, image):
        media_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        self._timestamp_ms += 1
        result = self._landmarker.detect_for_video(media_image, self._timestamp_ms)
        return SimpleNamespace(
            multi_hand_landmarks=result.hand_landmarks or [],
            multi_handedness=result.handedness or [],
        )

    def close(self):
        self._landmarker.close()