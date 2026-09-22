"""
Trains the SPEECH/LINGUISTIC sub-model on
data/Labeled_speech_data.csv (300 labeled samples: 100 HC, 100 MCI, and
100 Dementia, each with linguistic features already computed from speech
transcripts).

Only features that NeuroSense can genuinely recompute at inference time
from a live transcript are used (see services/linguistic_features.py) —
Converted-MMSE is intentionally excluded because the live app has no way
to produce a real MMSE score, and including it would create a feature the
model needs but the app can never actually supply.

Run:
    python train_speech_model.py

Artifacts written to ml/artifacts/:
    speech_xgb_model.json
    speech_feature_list.json
    speech_metrics.json
    speech_class_map.json
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
import xgboost as xgb

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.join(HERE, "data", "Labeled_speech_data.csv")
ARTIFACT_DIR = os.path.join(HERE, "artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

FEATURES = [
    "filler_count", "token_count", "type_count", "type_token_ratio",
    "ma_ttr", "brunets_index", "content_density", "repetitions",
    "sentence_count", "average_words_per_sentence", "total_seconds",
]
TARGET_COL = "Class_label"  # 0 = HC, 1 = MCI, 2 = Dementia
CLASS_MAP = {0: "HC", 1: "MCI", 2: "Dementia"}


def train():
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=FEATURES + [TARGET_COL])

    X = df[FEATURES].apply(pd.to_numeric, errors="coerce").fillna(0)
    y = df[TARGET_COL].astype(int)

    # Keep the class proportions stable in the holdout set and use modest tree depth to
    # limit overfitting, and we report metrics honestly rather than
    # overselling performance on such a small sample.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=3,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    metrics = {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "macro_f1": round(f1_score(y_test, preds, average="macro"), 4),
        "classification_report": classification_report(
            y_test, preds, target_names=["HC", "MCI", "Dementia"], output_dict=True, zero_division=0
        ),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "note": (
            "Trained on 300 labeled samples from data/Labeled_speech_data.csv; "
            "treat as an illustrative sub-model, not a clinically validated classifier."
        ),
    }
    print("Speech/linguistic model metrics:", json.dumps(metrics, indent=2, default=str))

    model.save_model(os.path.join(ARTIFACT_DIR, "speech_xgb_model.json"))
    with open(os.path.join(ARTIFACT_DIR, "speech_feature_list.json"), "w") as f:
        json.dump(FEATURES, f, indent=2)
    with open(os.path.join(ARTIFACT_DIR, "speech_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    with open(os.path.join(ARTIFACT_DIR, "speech_class_map.json"), "w") as f:
        json.dump(CLASS_MAP, f, indent=2)

    return model, metrics


if __name__ == "__main__":
    train()