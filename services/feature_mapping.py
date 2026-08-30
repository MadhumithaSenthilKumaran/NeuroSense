"""
Translates raw Lifestyle Questionnaire (Module 3) + Self-Reported Concerns
(Module 4) answers into the exact numeric encoding the clinical XGBoost
model was trained on (ml/data/alzheimers_disease_data.csv), so the live
app can call services/ml_model.predict_clinical() with real user data.

Reference ranges observed in the training data:
  AlcoholConsumption   0-20 (drinks/week, continuous)
  PhysicalActivity     0-10 (hours/week, continuous)
  DietQuality          0-10 (continuous, higher = healthier)
  SleepQuality         4-10 (continuous, higher = better)
  Gender               0/1, Smoking 0/1, *_flag columns 0/1
"""


def _flag(value_yes: bool) -> int:
    return 1 if value_yes else 0


def _education_level(value) -> int:
    try:
        years = float(value or 0)
    except (TypeError, ValueError):
        years = 0
    return min(3, max(0, int(years // 5)))


def map_questionnaire_to_clinical_features(answers: dict, concern_answers: dict = None) -> dict:
    concern_answers = concern_answers or {}

    smoking = answers.get("smoking")
    alcohol = answers.get("alcohol")
    exercise_days = answers.get("exercise_days")
    sleep_quality = answers.get("sleep_quality")
    diet_quality = answers.get("diet_quality")
    physical_activity = answers.get("physical_activity")

    # --- Categorical -> continuous approximations, on the training scale ---
    alcohol_map = {"Never": 0.5, "Occasionally": 4.0, "Weekly": 9.0, "Daily": 16.0}
    diet_map = {"Poor": 1.5, "Fair": 4.0, "Good": 6.5, "Excellent": 9.0}
    sleep_map = {"Poor": 4.5, "Fair": 6.0, "Good": 7.5, "Excellent": 9.0}
    activity_map = {"Sedentary": 0.5, "Light": 3.0, "Moderate": 6.0, "Active": 9.0}

    features = {
        "Age": float(answers.get("age") or 0),
        "Gender": 1 if str(answers.get("gender", "")).lower().startswith("f") else 0,
        "Ethnicity": 0,  # not collected — self-reported ethnicity intentionally excluded from UI
        "EducationLevel": _education_level(answers.get("education_years")),
        "BMI": float(answers.get("bmi")) if answers.get("bmi") not in (None, "") else 24.0,
        "Smoking": 1 if smoking == "Current smoker" else 0,
        "AlcoholConsumption": alcohol_map.get(alcohol, 4.0),
        "PhysicalActivity": activity_map.get(physical_activity, exercise_days_to_hours(exercise_days)),
        "DietQuality": diet_map.get(diet_quality, 5.0),
        "SleepQuality": sleep_map.get(sleep_quality, 6.0),
        "FamilyHistoryAlzheimers": _flag(answers.get("family_history") == "Yes"),
        "CardiovascularDisease": _flag(answers.get("heart_disease") == "Yes"),
        "Diabetes": _flag(answers.get("diabetes") in ("Yes", "Pre-diabetic")),
        "Depression": _flag(answers.get("depression") in ("Current", "Past")),
        "HeadInjury": 0,  # not collected in questionnaire spec — default no
        "Hypertension": _flag(str(answers.get("hypertension", "")).startswith("Yes")),
        # Blood pressure / cholesterol panels and MMSE/ADL/FunctionalAssessment
        # are NOT collected anywhere in the NeuroSense UI (no clinical labs,
        # no formal MMSE). Rather than guessing plausible-looking numbers —
        # which would silently bias the prediction — these are left out of
        # the dict entirely. predict_clinical() imputes any missing field
        # with the training population's mean, which is the honest neutral
        # choice for something we genuinely don't measure.
        "MMSE": None,
        "FunctionalAssessment": None,
        "MemoryComplaints": _flag(answers.get("memory_complaints") in ("Occasionally", "Frequently")),
        "BehavioralProblems": _flag(
            concern_answers.get("difficulty_making_decisions") in ("Often", "Very Often")
        ),
        "ADL": None,
        "Confusion": _flag(concern_answers.get("difficulty_following_conversations") in ("Often", "Very Often")),
        "Disorientation": _flag(concern_answers.get("difficulty_recognizing_places") in ("Often", "Very Often")),
        "PersonalityChanges": 0,
        "DifficultyCompletingTasks": _flag(answers.get("daily_task_difficulty") in ("Occasionally", "Frequently")),
        "Forgetfulness": _flag(
            concern_answers.get("forget_appointments") in ("Often", "Very Often")
            or concern_answers.get("repeat_questions") in ("Often", "Very Often")
        ),
    }

    # Drop None placeholders (predict_clinical treats missing keys as 0,
    # which for these particular unmeasured clinical scores would bias the
    # model toward "healthy" — since we can't measure MMSE/ADL/Functional
    # Assessment in-app, we exclude them so the trained model's own
    # imputation via the scaler's centering handles them more neutrally).
    return {k: v for k, v in features.items() if v is not None}


def exercise_days_to_hours(exercise_days):
    try:
        d = float(exercise_days)
    except (TypeError, ValueError):
        return 3.0
    return round(d * 1.1, 1)  # rough days/week -> hours/week estimate