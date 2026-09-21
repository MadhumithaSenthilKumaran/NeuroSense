"""
Combines the four modalities into one final risk assessment:

  1. Clinical/lifestyle XGBoost model (trained on 2,149 real patient
     records) — the primary, best-validated signal.
  2. Speech/linguistic XGBoost model (trained on 157 transcript-derived
     samples) — used only when a transcript was produced.
  3. Cognitive test battery (memory, reaction time, attention, visual
     memory, pattern recognition, orientation) — rule-based composite,
     see services/cognitive_scoring.py.
  4. Self-reported concern score — rule-based composite, see
     services/lifestyle_scoring.py.

Why a weighted ensemble rather than one end-to-end model: no public
dataset exists with all four modalities collected on the *same* people, so
a single jointly-trained fusion model isn't honestly trainable from what's
available here. This ensemble is a transparent, documented stand-in — the
weights are a reasonable prototype default, not a clinically validated
formula. Retraining a true joint model requires a multimodal dataset.
"""

from services.ml_model import predict_clinical, predict_speech

# Relative trust in each modality. Clinical model carries the most weight
# because it's trained on the largest, most reliable labeled dataset.
WEIGHTS = {
    "cognitive": 0.40,
    "speech": 0.25,
    "lifestyle_stress": 0.15,
    "self_reported_concerns": 0.10,
    "response_consistency": 0.10,
}

CLINICAL_FEATURE_MAP = {
    # Maps NeuroSense lifestyle-questionnaire field -> clinical model feature.
    "age": "Age",
    "gender_code": "Gender",
    "ethnicity_code": "Ethnicity",
    "education_level_code": "EducationLevel",
    "bmi": "BMI",
    "smoking_code": "Smoking",
    "alcohol_units": "AlcoholConsumption",
    "physical_activity_score": "PhysicalActivity",
    "diet_quality_score": "DietQuality",
    "sleep_quality_score": "SleepQuality",
    "family_history_flag": "FamilyHistoryAlzheimers",
    "cardiovascular_flag": "CardiovascularDisease",
    "diabetes_flag": "Diabetes",
    "depression_flag": "Depression",
    "head_injury_flag": "HeadInjury",
    "hypertension_flag": "Hypertension",
    "memory_complaints_flag": "MemoryComplaints",
    "behavioral_problems_flag": "BehavioralProblems",
    "confusion_flag": "Confusion",
    "disorientation_flag": "Disorientation",
    "personality_changes_flag": "PersonalityChanges",
    "difficulty_completing_tasks_flag": "DifficultyCompletingTasks",
    "forgetfulness_flag": "Forgetfulness",
}


def risk_class_from_probability(p: float) -> str:
    if p < 0.33:
        return "Low"
    if p < 0.66:
        return "Moderate"
    return "High"


def fuse(clinical_features: dict, speech_linguistic_features: dict,
         cognitive_overall_score: float, concern_score: float,
         lifestyle_stress_score: float = None,
         response_consistency_score: float = None):
    """
    Returns:
      {
        "risk_probability": float 0-1,
        "risk_class": "Low"|"Moderate"|"High",
        "modality_scores": {...},
        "shap_top_features": [...],
        "used_modalities": [...]
      }
    """
    components = {}
    shap_features = []
    used = []

    # 1. Clinical model (always available — the questionnaire is mandatory)
    clinical_proba, clinical_contrib = predict_clinical(clinical_features)
    shap_features.extend([
        {"feature": f, "modality": "clinical", "shap_value": round(v, 4)}
        for f, v in clinical_contrib[:5]
    ])

    # 2. Speech model (only if transcript-derived linguistic features exist)
    if speech_linguistic_features:
        speech_proba, _dist, speech_contrib = predict_speech(speech_linguistic_features)
        components["speech"] = speech_proba
        used.append("speech")
        shap_features.extend([
            {"feature": f, "modality": "speech", "shap_value": round(v, 4)}
            for f, v in speech_contrib[:3]
        ])

    # 3. Cognitive composite (0-100, higher = better -> invert to risk 0-1)
    if cognitive_overall_score is not None:
        components["cognitive"] = 1 - (cognitive_overall_score / 100)
        used.append("cognitive")
        shap_features.append({
            "feature": "Cognitive test composite",
            "modality": "cognitive",
            "shap_value": round(components["cognitive"], 4),
        })

    # 4. Concern composite (0-100, higher = more concern -> risk directly)
    if concern_score is not None:
        components["self_reported_concerns"] = concern_score / 100
        used.append("self_reported_concerns")
        shap_features.append({
            "feature": "Self-reported concern composite",
            "modality": "concern",
            "shap_value": round(components["self_reported_concerns"], 4),
        })

    if lifestyle_stress_score is not None:
        components["lifestyle_stress"] = lifestyle_stress_score / 100
        used.append("lifestyle_stress")
        shap_features.append({"feature": "Lifestyle stress risk", "modality": "lifestyle_stress", "shap_value": round(components["lifestyle_stress"], 4)})

    if response_consistency_score is not None:
        components["response_consistency"] = 1 - (response_consistency_score / 100)
        used.append("response_consistency")
        shap_features.append({"feature": "Response consistency", "modality": "response_consistency", "shap_value": round(components["response_consistency"], 4)})

    total_weight = sum(WEIGHTS[k] for k in components)
    risk_probability = sum(components[k] * WEIGHTS[k] for k in components) / total_weight

    shap_features.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

    return {
        "risk_probability": round(risk_probability, 4),
        "risk_class": risk_class_from_probability(risk_probability),
        "modality_scores": {k: round(v, 4) for k, v in components.items()},
        "shap_top_features": shap_features[:8],
        "used_modalities": used,
    }