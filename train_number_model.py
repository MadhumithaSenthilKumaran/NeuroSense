"""Train the finger-number classifier from data/Numbers/<number>/ images."""

import json
from pathlib import Path

import cv2
import numpy as np
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
import xgboost as xgb
from services.mediapipe_hands import create_hands

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "Numbers"
ARTIFACT_DIR = ROOT / "artifacts"
FEATURES = [f"landmark_{index}_{axis}" for index in range(21) for axis in "xyz"]
MAX_IMAGES_PER_CLASS = 200


def extract_landmarks(image, hands):
    result = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    if not result.multi_hand_landmarks:
        return None
    detected_hand = result.multi_hand_landmarks[0]
    points = getattr(detected_hand, "landmark", detected_hand)
    wrist = np.array([points[0].x, points[0].y, points[0].z], dtype=np.float32)
    values = np.array([[point.x, point.y, point.z] for point in points], dtype=np.float32)
    return (values - wrist).reshape(-1)


def train():
    if not DATA_DIR.is_dir():
        raise FileNotFoundError(f"Dataset not found: {DATA_DIR}. Add Numbers/1 through Numbers/9 first.")
    rows, labels = [], []
    hands = create_hands()
    try:
        for label_dir in sorted(DATA_DIR.iterdir(), key=lambda path: int(path.name) if path.name.isdigit() else 999):
            if not label_dir.is_dir() or not label_dir.name.isdigit():
                continue
            for image_path in sorted(label_dir.iterdir())[:MAX_IMAGES_PER_CLASS]:
                image = cv2.imread(str(image_path))
                if image is None:
                    continue
                features = extract_landmarks(image, hands)
                if features is not None:
                    rows.append(features)
                    labels.append(int(label_dir.name))
    finally:
        hands.close()
    if len(set(labels)) < 2 or len(rows) < 20:
        raise ValueError("Need at least 20 readable hand images across two or more numbered folders.")
    classes = sorted(set(labels))
    label_ids = {label: index for index, label in enumerate(classes)}
    encoded_labels = np.asarray([label_ids[label] for label in labels])
    x_train, x_test, y_train, y_test = train_test_split(
        np.asarray(rows), encoded_labels, test_size=0.2, random_state=42, stratify=encoded_labels
    )
    model = xgb.XGBClassifier(
        n_estimators=160, max_depth=4, learning_rate=0.08, subsample=0.85,
        colsample_bytree=0.85, objective="multi:softprob", num_class=len(set(labels)),
        eval_metric="mlogloss", random_state=42,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    metrics = {
        "accuracy": round(accuracy_score(y_test, predictions), 4),
        "classification_report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
        "n_train": len(x_train), "n_test": len(x_test), "classes": classes,
    }
    ARTIFACT_DIR.mkdir(exist_ok=True)
    model.save_model(str(ARTIFACT_DIR / "number_xgb_model.json"))
    (ARTIFACT_DIR / "number_feature_list.json").write_text(json.dumps(FEATURES, indent=2))
    (ARTIFACT_DIR / "number_class_map.json").write_text(json.dumps({str(index): label for label, index in label_ids.items()}, indent=2))
    (ARTIFACT_DIR / "number_metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    print(json.dumps(metrics, indent=2, default=str))
    return model, metrics


if __name__ == "__main__":
    train()