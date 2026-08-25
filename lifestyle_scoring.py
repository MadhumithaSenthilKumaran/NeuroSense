"""
Module 3: Lifestyle Questionnaire (25 questions) and
Module 4: Self-Reported Cognitive Concerns (10 items).

Each lifestyle question carries a `risk_direction` used to fold its answer
into a single 0-100 lifestyle_score, where 100 = best modifiable-risk
profile and 0 = worst. This weighting is a reasonable, transparent
heuristic for a screening prototype — it is NOT a validated clinical
instrument and should be reviewed by a clinician/epidemiologist before
any real-world use.
"""

LIFESTYLE_QUESTIONS = [
    {"id": "age", "text": "What is your age?", "type": "number"},
    {"id": "education_years", "text": "Years of formal education", "type": "number"},
    {"id": "smoking", "text": "Do you currently smoke?", "type": "radio",
     "options": ["Never", "Former smoker", "Current smoker"]},
    {"id": "alcohol", "text": "How often do you drink alcohol?", "type": "radio",
     "options": ["Never", "Occasionally", "Weekly", "Daily"]},
    {"id": "exercise_days", "text": "Days per week you exercise", "type": "slider", "min": 0, "max": 7},
    {"id": "sleep_hours", "text": "Average hours of sleep per night", "type": "slider", "min": 2, "max": 12},
    {"id": "sleep_quality", "text": "How would you rate your sleep quality?", "type": "radio",
     "options": ["Poor", "Fair", "Good", "Excellent"]},
    {"id": "stress_level", "text": "Rate your typical stress level", "type": "slider", "min": 0, "max": 10},
    {"id": "diet_quality", "text": "How healthy is your typical diet?", "type": "radio",
     "options": ["Poor", "Fair", "Good", "Excellent"]},
    {"id": "social_interaction", "text": "How often do you socialize with others?", "type": "radio",
     "options": ["Rarely", "Monthly", "Weekly", "Daily"]},
    {"id": "reading_habit", "text": "How often do you read or do mentally engaging activities?",
     "type": "radio", "options": ["Rarely", "Monthly", "Weekly", "Daily"]},
    {"id": "family_history", "text": "Family history of Alzheimer's disease?", "type": "radio",
     "options": ["No", "Not sure", "Yes"]},
    {"id": "diabetes", "text": "Do you have diabetes?", "type": "radio", "options": ["No", "Pre-diabetic", "Yes"]},
    {"id": "hypertension", "text": "Do you have hypertension (high blood pressure)?", "type": "radio",
     "options": ["No", "Yes, controlled", "Yes, uncontrolled"]},
    {"id": "heart_disease", "text": "Do you have a heart disease diagnosis?", "type": "radio",
     "options": ["No", "Yes"]},
    {"id": "depression", "text": "Have you been diagnosed with depression?", "type": "radio",
     "options": ["No", "Past", "Current"]},
    {"id": "hearing_loss", "text": "Do you experience hearing loss?", "type": "radio",
     "options": ["No", "Mild", "Moderate/Severe"]},
    {"id": "physical_activity", "text": "General physical activity level", "type": "radio",
     "options": ["Sedentary", "Light", "Moderate", "Active"]},
    {"id": "bmi", "text": "What is your BMI? (leave blank if unknown)", "type": "number"},
    {"id": "medication_count", "text": "Number of daily medications", "type": "number"},
    {"id": "memory_complaints", "text": "Do you personally notice memory problems?", "type": "radio",
     "options": ["No", "Occasionally", "Frequently"]},
    {"id": "word_finding_difficulty", "text": "Difficulty finding the right words?", "type": "radio",
     "options": ["No", "Occasionally", "Frequently"]},
    {"id": "name_recall_difficulty", "text": "Difficulty remembering names?", "type": "radio",
     "options": ["No", "Occasionally", "Frequently"]},
    {"id": "finance_difficulty", "text": "Difficulty managing finances?", "type": "radio",
     "options": ["No", "Occasionally", "Frequently"]},
    {"id": "daily_task_difficulty", "text": "Difficulty completing familiar daily tasks?", "type": "radio",
     "options": ["No", "Occasionally", "Frequently"]},
]

CONCERN_QUESTIONS = [
    {"id": "forget_appointments", "text": "Forget appointments"},
    {"id": "lose_belongings", "text": "Lose belongings"},
    {"id": "forget_conversations", "text": "Forget conversations"},
    {"id": "repeat_questions", "text": "Repeat questions"},
    {"id": "need_reminders", "text": "Need reminders"},
    {"id": "difficulty_concentrating", "text": "Difficulty concentrating"},
    {"id": "difficulty_following_conversations", "text": "Difficulty following conversations"},
    {"id": "difficulty_making_decisions", "text": "Difficulty making decisions"},
    {"id": "difficulty_planning", "text": "Difficulty planning"},
    {"id": "difficulty_recognizing_places", "text": "Difficulty recognizing familiar places"},
]
CONCERN_SCALE = ["Never", "Rarely", "Sometimes", "Often", "Very Often"]

# --- Risk scoring tables (0 = best, 1 = worst) for categorical answers ---
_CATEGORICAL_RISK = {
    "smoking": {"Never": 0.0, "Former smoker": 0.4, "Current smoker": 1.0},
    "alcohol": {"Never": 0.1, "Occasionally": 0.0, "Weekly": 0.4, "Daily": 1.0},
    "sleep_quality": {"Poor": 1.0, "Fair": 0.6, "Good": 0.25, "Excellent": 0.0},
    "diet_quality": {"Poor": 1.0, "Fair": 0.6, "Good": 0.25, "Excellent": 0.0},
    "social_interaction": {"Rarely": 1.0, "Monthly": 0.6, "Weekly": 0.25, "Daily": 0.0},
    "reading_habit": {"Rarely": 1.0, "Monthly": 0.6, "Weekly": 0.25, "Daily": 0.0},
    "family_history": {"No": 0.0, "Not sure": 0.4, "Yes": 1.0},
    "diabetes": {"No": 0.0, "Pre-diabetic": 0.5, "Yes": 1.0},
    "hypertension": {"No": 0.0, "Yes, controlled": 0.4, "Yes, uncontrolled": 1.0},
    "heart_disease": {"No": 0.0, "Yes": 1.0},
    "depression": {"No": 0.0, "Past": 0.4, "Current": 1.0},
    "hearing_loss": {"No": 0.0, "Mild": 0.4, "Moderate/Severe": 1.0},
    "physical_activity": {"Sedentary": 1.0, "Light": 0.6, "Moderate": 0.25, "Active": 0.0},
    "memory_complaints": {"No": 0.0, "Occasionally": 0.5, "Frequently": 1.0},
    "word_finding_difficulty": {"No": 0.0, "Occasionally": 0.5, "Frequently": 1.0},
    "name_recall_difficulty": {"No": 0.0, "Occasionally": 0.5, "Frequently": 1.0},
    "finance_difficulty": {"No": 0.0, "Occasionally": 0.5, "Frequently": 1.0},
    "daily_task_difficulty": {"No": 0.0, "Occasionally": 0.5, "Frequently": 1.0},
}

_CONCERN_RISK = {"Never": 0.0, "Rarely": 0.25, "Sometimes": 0.5, "Often": 0.75, "Very Often": 1.0}


def _numeric_risk(value, low, high, invert=False):
    """Map a numeric value into 0-1 risk, clamped. invert=True means higher value = lower risk."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.3  # neutral-ish default for missing data
    v = max(low, min(high, v))
    frac = (v - low) / (high - low) if high != low else 0
    return (1 - frac) if invert else frac


def score_lifestyle(answers: dict) -> dict:
    risks = []

    risks.append(_numeric_risk(answers.get("age"), 40, 90))
    risks.append(_numeric_risk(answers.get("education_years"), 0, 20, invert=True))
    risks.append(_numeric_risk(answers.get("exercise_days"), 0, 7, invert=True))

    sleep_hours = answers.get("sleep_hours")
    try:
        sh = float(sleep_hours)
        # U-shaped: ideal ~7-8h, penalize both too little and too much
        risks.append(min(1.0, abs(sh - 7.5) / 5))
    except (TypeError, ValueError):
        risks.append(0.3)

    risks.append(_numeric_risk(answers.get("stress_level"), 0, 10))

    bmi = answers.get("bmi")
    try:
        b = float(bmi)
        risks.append(0.0 if 18.5 <= b <= 24.9 else min(1.0, abs(b - 22) / 20))
    except (TypeError, ValueError):
        pass  # optional field

    med_count = answers.get("medication_count")
    if med_count not in (None, ""):
        risks.append(_numeric_risk(med_count, 0, 10))

    for field, table in _CATEGORICAL_RISK.items():
        val = answers.get(field)
        if val in table:
            risks.append(table[val])

    if not risks:
        return {"lifestyle_score": None, "risk_factor_count": 0}

    avg_risk = sum(risks) / len(risks)
    lifestyle_score = round(100 * (1 - avg_risk), 1)
    elevated = [
        f for f in _CATEGORICAL_RISK
        if answers.get(f) in _CATEGORICAL_RISK[f] and _CATEGORICAL_RISK[f][answers.get(f)] >= 0.6
    ]
    return {
        "lifestyle_score": lifestyle_score,
        "elevated_risk_factors": elevated,
    }


def score_concern(answers: dict) -> dict:
    risks = []
    for q in CONCERN_QUESTIONS:
        val = answers.get(q["id"])
        if val in _CONCERN_RISK:
            risks.append(_CONCERN_RISK[val])
    if not risks:
        return {"concern_score": None}
    avg = sum(risks) / len(risks)
    # concern_score: 0 = no concerns, 100 = maximum self-reported concern
    return {"concern_score": round(avg * 100, 1)}