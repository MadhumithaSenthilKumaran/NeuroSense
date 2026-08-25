"""
Loads the two trained XGBoost models (clinical/lifestyle + speech/linguistic)
and exposes prediction + SHAP explanation helpers. Models are lazy-loaded
and cached at module level so they're only read from disk once per process.
"""

import json
import os
import joblib
import numpy as np
import xgboost as xgb
import shap

from config import Config

_cache = {}


def _artifact(name):
    return os.path.join(Config.MODEL_DIR, name)


def load_clinical_model():
    if "clinical_model" not in _cache:
        model = xgb.XGBClassifier()
        model.load_model(_artifact("clinical_xgb_model.json"))
        _cache["clinical_model"] = model
        _cache["clinical_scaler"] = joblib.load(_artifact("clinical_scaler.pkl"))
        with open(_artifact("clinical_feature_list.json")) as f:
            _cache["clinical_features"] = json.load(f)
        _cache["clinical_explainer"] = shap.TreeExplainer(model)
    return (
        _cache["clinical_model"], _cache["clinical_scaler"],
        _cache["clinical_features"], _cache["clinical_explainer"],
    )


def load_speech_model():
    if "speech_model" not in _cache:
        model = xgb.XGBClassifier()
        model.load_model(_artifact("speech_xgb_model.json"))
        _cache["speech_model"] = model
        with open(_artifact("speech_feature_list.json")) as f:
            _cache["speech_features"] = json.load(f)
        with open(_artifact("speech_class_map.json")) as f:
            _cache["speech_class_map"] = json.load(f)
        _cache["speech_explainer"] = shap.TreeExplainer(model)
    return (
        _cache["speech_model"], _cache["speech_features"],
        _cache["speech_class_map"], _cache["speech_explainer"],
    )


def predict_clinical(feature_dict: dict):
    """
    feature_dict must contain (a subset is fine). Fields NeuroSense cannot
    genuinely collect in-app (e.g. MMSE, ADL, FunctionalAssessment,
    cholesterol panels, blood pressure) are imputed with the TRAINING
    POPULATION MEAN, not 0 — several of these scales run low-to-high where
    0 is the worst possible score (e.g. MMSE, ADL), so defaulting to 0
    would systematically push every user's risk up and dominate every
    SHAP explanation with a non-personalized artifact. Mean-imputation
    keeps an unmeasured field's contribution close to neutral instead.
    Returns probability of Diagnosis=1 (Alzheimer's-consistent profile)
    plus a per-feature SHAP contribution list.
    """
    model, scaler, features, explainer = load_clinical_model()
    row = np.array(
        [[feature_dict[f] if f in feature_dict else scaler.mean_[i]
          for i, f in enumerate(features)]],
        dtype=float,
    )
    row_scaled = scaler.transform(row)

    proba = float(model.predict_proba(row_scaled)[0][1])
    shap_values = explainer.shap_values(row_scaled)
    if isinstance(shap_values, list):  # some SHAP versions return a list per class
        shap_values = shap_values[1]
    contributions = sorted(
        (
            (f, v) for f, v in zip(features, shap_values[0].tolist())
            if f in feature_dict  # only show factors the user actually provided
        ),
        key=lambda x: abs(x[1]), reverse=True,
    )
    return proba, contributions


def predict_speech(feature_dict: dict):
    """
    Returns P(MCI) + P(Dementia) as a single "linguistic risk" probability,
    the full class distribution, and SHAP contributions for the predicted
    class.
    """
    model, features, class_map, explainer = load_speech_model()
    row = np.array([[feature_dict.get(f, 0) for f in features]], dtype=float)

    proba = model.predict_proba(row)[0]  # [P(HC), P(MCI), P(Dementia)]
    risk_proba = float(proba[1] + proba[2])

    shap_values = explainer.shap_values(row)
    predicted_class = int(np.argmax(proba))
    if isinstance(shap_values, list):
        class_shap = shap_values[predicted_class][0]
    else:
        # newer shap returns array shaped (n_samples, n_features, n_classes)
        class_shap = shap_values[0, :, predicted_class] if shap_values.ndim == 3 else shap_values[0]

    contributions = sorted(
        zip(features, class_shap.tolist()),
        key=lambda x: abs(x[1]), reverse=True,
    )
    return risk_proba, {class_map[str(i)]: round(float(p), 4) for i, p in enumerate(proba)}, contributions