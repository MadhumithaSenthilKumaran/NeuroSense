"""
Retrieval-Augmented recommendation engine.

Retrieval: tag-overlap scoring against the local knowledge base
(knowledge_base/kb_data.py). This is intentionally simple (no external
LLM/embedding API key is available in this environment) but the function
signature mirrors a real RAG pipeline so swapping in a vector store and an
LLM call later is a drop-in replacement — see the docstring in kb_data.py.

Generation: template-based personalized copy assembled from the retrieved
snippets plus the user's actual risk drivers (SHAP top features + elevated
lifestyle factors). Every explanation ends with the mandatory
non-diagnostic disclaimer.
"""

from knowledge_base.kb_data import KNOWLEDGE_BASE

DISCLAIMER = (
    "This assessment is not a medical diagnosis. Please consult a "
    "qualified neurologist or healthcare professional."
)

_RISK_FACTOR_TAGS = {
    "smoking": "smoking",
    "alcohol": "alcohol",
    "exercise_days": "exercise",
    "physical_activity": "physical_activity",
    "sleep_hours": "sleep",
    "sleep_quality": "sleep",
    "stress_level": "stress",
    "diet_quality": "diet",
    "social_interaction": "social_interaction",
    "reading_habit": "reading_habit",
    "hearing_loss": "hearing_loss",
    "hypertension": "hypertension",
    "diabetes": "diabetes",
    "heart_disease": "cardiovascular_flag",
    "memory_complaints": "memory_complaints",
    "word_finding_difficulty": "word_finding_difficulty",
}


def retrieve(tags: list, top_k: int = 5):
    scored = []
    tagset = set(tags)
    for entry in KNOWLEDGE_BASE:
        overlap = len(tagset & set(entry["tags"]))
        if overlap > 0:
            scored.append((overlap, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        # fall back to general guidance
        scored = [(0, e) for e in KNOWLEDGE_BASE if "general" in e["tags"]]
    return [entry for _, entry in scored[:top_k]]


def _plain_english_shap_summary(shap_top_features: list) -> str:
    if not shap_top_features:
        return "No single factor dominated the prediction; the result reflects a broad combination of inputs."
    readable = {
        "MemoryComplaints": "self-reported memory concerns",
        "BehavioralProblems": "reported behavioral changes",
        "MMSE": "cognitive screening score",
        "PhysicalActivity": "physical activity level",
        "ADL": "reported daily-living difficulty",
        "Confusion": "reported confusion",
        "Disorientation": "reported disorientation",
        "Forgetfulness": "reported forgetfulness",
        "SleepQuality": "sleep quality",
        "DietQuality": "diet quality",
        "AlcoholConsumption": "alcohol consumption",
        "Smoking": "smoking status",
        "Age": "age",
        "Hypertension": "blood pressure status",
        "Diabetes": "diabetes status",
        "CardiovascularDisease": "cardiovascular health",
        "average_words_per_sentence": "sentence complexity in speech",
        "ma_ttr": "vocabulary variety in speech",
        "brunets_index": "lexical richness in speech",
        "filler_count": "use of filler words in speech",
        "total_seconds": "speaking duration",
        "Cognitive test composite": "overall cognitive test performance",
        "Self-reported concern composite": "self-reported day-to-day concerns",
    }
    top = shap_top_features[:3]
    phrases = []
    for item in top:
        label = readable.get(item["feature"], item["feature"].replace("_", " "))
        direction = "increased" if item["shap_value"] > 0 else "lowered"
        phrases.append(f"{label} ({direction} the estimated risk)")
    return "The factors that most influenced this result were: " + "; ".join(phrases) + "."


def generate_recommendations(risk_class: str, shap_top_features: list,
                              elevated_lifestyle_factors: list) -> dict:
    tags = [_RISK_FACTOR_TAGS[f] for f in elevated_lifestyle_factors if f in _RISK_FACTOR_TAGS]
    if not tags:
        tags = ["exercise", "diet", "sleep", "social_interaction"]
    retrieved = retrieve(tags, top_k=5)

    explanation = _plain_english_shap_summary(shap_top_features)

    urgency = {
        "Low": "Your current profile shows a relatively low estimated risk pattern. Keep up protective habits.",
        "Moderate": "Your profile shows some elevated risk factors worth attention and monitoring over time.",
        "High": "Your profile shows several elevated risk factors. We recommend prioritizing a clinical consultation.",
    }.get(risk_class, "")

    categories = {"lifestyle": [], "diet": [], "exercise": [], "sleep": [], "memory": [], "consultation": []}
    for entry in retrieved:
        text = f"{entry['text']} (Source: {entry['source']})"
        if "diet" in entry["tags"] or "nutrition" in entry["tags"]:
            categories["diet"].append(text)
        elif "exercise" in entry["tags"] or "physical_activity" in entry["tags"]:
            categories["exercise"].append(text)
        elif "sleep" in entry["tags"]:
            categories["sleep"].append(text)
        elif "memory_complaints" in entry["tags"] or "word_finding_difficulty" in entry["tags"]:
            categories["memory"].append(text)
        elif "general" in entry["tags"]:
            categories["consultation"].append(text)
        else:
            categories["lifestyle"].append(text)

    if risk_class in ("Moderate", "High") and not categories["consultation"]:
        categories["consultation"].append(
            "Persistent or worsening memory or thinking changes warrant evaluation by a physician "
            "or neurologist who can order appropriate clinical testing. (Source: NIA)"
        )

    return {
        "summary": urgency,
        "explanation": explanation,
        "diet_suggestions": categories["diet"],
        "exercise_recommendations": categories["exercise"],
        "sleep_recommendations": categories["sleep"],
        "memory_improvement_tips": categories["memory"],
        "lifestyle_recommendations": categories["lifestyle"],
        "medical_consultation_guidance": categories["consultation"] or [
            "If you have any concerns about your memory or thinking, discussing them with a "
            "physician is a reasonable next step regardless of this screening result."
        ],
        "disclaimer": DISCLAIMER,
    }