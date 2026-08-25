"""
Trains the PRIMARY risk model on ml/data/alzheimers_disease_data.csv
(2,149 real patient records with a genuine `Diagnosis` label).

This model consumes clinical + lifestyle + self-reported concern style
features — i.e. everything NeuroSense's Lifestyle Questionnaire (Module 3)
and Self-Reported Concerns (Module 4) map onto directly.

Run:
    cd backend
    python -m ml.train_clinical_model

Artifacts written to ml/artifacts/:
    clinical_xgb_model.json
    clinical_scaler.pkl
    clinical_feature_list.json
    clinical_metrics.json
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix,
)
import xgboost as xgb

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.join(HERE, "data", "alzheimers_disease_data.csv")
ARTIFACT_DIR = os.path.join(HERE, "artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

DROP_COLS = ["PatientID", "DoctorInCharge", "Diagnosis"]
TARGET_COL = "Diagnosis"


def load_and_prepare():
    df = pd.read_csv(DATA_PATH)
    df = df.drop_duplicates()

    y = df[TARGET_COL].astype(int)
    X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])

    # All remaining columns are already numeric (binary flags 0/1 or
    # continuous clinical measurements) — no additional encoding needed.
    feature_list = X.columns.tolist()
    return X, y, feature_list


def train():
    X, y, feature_list = load_and_prepare()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=2,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train)

    proba = model.predict_proba(X_test_scaled)[:, 1]
    preds = (proba >= 0.5).astype(int)

    metrics = {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "precision": round(precision_score(y_test, preds), 4),
        "recall": round(recall_score(y_test, preds), 4),
        "f1_score": round(f1_score(y_test, preds), 4),
        "roc_auc": round(roc_auc_score(y_test, proba), 4),
        "confusion_matrix": confusion_matrix(y_test, preds).tolist(),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "positive_rate": round(float(y.mean()), 4),
    }
    print("Clinical/Lifestyle model metrics:", json.dumps(metrics, indent=2))

    model.save_model(os.path.join(ARTIFACT_DIR, "clinical_xgb_model.json"))
    joblib.dump(scaler, os.path.join(ARTIFACT_DIR, "clinical_scaler.pkl"))
    with open(os.path.join(ARTIFACT_DIR, "clinical_feature_list.json"), "w") as f:
        json.dump(feature_list, f, indent=2)
    with open(os.path.join(ARTIFACT_DIR, "clinical_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    return model, scaler, feature_list, metrics


if __name__ == "__main__":
    train()