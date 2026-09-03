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

import json
import os
from urllib.request import Request, urlopen

from knowledge_base.kb_data import KNOWLEDGE_BASE

DISCLAIMER = (
    "This assessment is not a medical diagnosis. Please consult a "
    "qualified neurologist or healthcare professional."
)


def _llm_refine(prompt: str):
    api_key = os.environ.get("LLM_API_KEY", "")
    if not api_key:
        return None
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = json.dumps({
        "model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "Give concise, non-diagnostic health screening guidance."},
            {"role": "user", "content": prompt},
        ],
    }).encode("utf-8")
    request = Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None

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
        tags = ["exercise", "diet", "sleep", "stress", "social_interaction"]
    retrieved = retrieve(tags, top_k=6)

    explanation = _plain_english_shap_summary(shap_top_features)

    urgency = {
        "Low": "Your current profile shows a relatively low estimated risk pattern. Keep up protective habits and consider a routine follow-up review.",
        "Moderate": "Your profile shows some elevated risk factors worth attention and monitoring over time. A targeted follow-up is useful.",
        "High": "Your profile shows several elevated risk factors. We recommend prioritizing a clinical consultation and a follow-up assessment soon.",
    }.get(risk_class, "")

    categories = {"lifestyle": [], "diet": [], "exercise": [], "sleep": [], "memory": [], "stress": [], "consultation": []}
    for entry in retrieved:
        text = f"{entry['text']} (Source: {entry['source']})"
        if "diet" in entry["tags"] or "nutrition" in entry["tags"]:
            categories["diet"].append(text)
        elif "exercise" in entry["tags"] or "physical_activity" in entry["tags"]:
            categories["exercise"].append(text)
        elif "sleep" in entry["tags"]:
            categories["sleep"].append(text)
        elif "stress" in entry["tags"]:
            categories["stress"].append(text)
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

    next_assessment_suggestion = {
        "Low": "Plan the next assessment in 6 months to monitor trends and keep early changes visible.",
        "Moderate": "Plan the next assessment in 3 months to re-check memory, lifestyle, and speech patterns over time.",
        "High": "Schedule the next assessment within 4-6 weeks and consult a clinician if symptoms change or worsen.",
    }.get(risk_class, "Plan the next assessment in 3 months to track progress and catch changes early.")

    llm_summary = _llm_refine(
        "Create a two-sentence personalized recommendation from this retrieved evidence and risk context. "
        f"Risk class: {risk_class}. Evidence: {[entry['text'] for entry in retrieved]}. "
        f"Drivers: {elevated_lifestyle_factors}."
    )

    return {
        "summary": llm_summary or urgency,
        "explanation": explanation,
        "diet_suggestions": categories["diet"],
        "exercise_recommendations": categories["exercise"],
        "sleep_recommendations": categories["sleep"],
        "stress_reduction_recommendations": categories["stress"],
        "memory_improvement_tips": categories["memory"],
        "lifestyle_recommendations": categories["lifestyle"],
        "medical_consultation_guidance": categories["consultation"] or [
            "If you have any concerns about your memory or thinking, discussing them with a "
            "physician is a reasonable next step regardless of this screening result."
        ],
        "next_assessment_suggestion": next_assessment_suggestion,
        "disclaimer": DISCLAIMER,
    }


def generate_longitudinal_recommendations(sessions: list) -> dict:
    """Use retrieved guidance plus observed changes to personalize a cycle summary."""
    scores = [s.get("modality_scores", {}) for s in sessions]
    cognitive = [s.get("cognitive_score") for s in sessions if s.get("cognitive_score") is not None]
    speech = [s.get("speech_score") for s in sessions if s.get("speech_score") is not None]
    tags = ["memory_complaints", "sleep", "stress"] if cognitive and cognitive[-1] < cognitive[0] else ["exercise", "social_interaction"]
    retrieved = retrieve(tags, top_k=4)
    direction = "improved" if cognitive and cognitive[-1] > cognitive[0] else "changed" if cognitive else "was recorded"
    return {
        "summary": f"Across the completed sessions, cognitive performance {direction}; recommendations reflect the measured pattern and reported factors.",
        "recommendations": [entry["text"] for entry in retrieved],
        "cognitive_scores": cognitive,
        "speech_scores": speech,
        "risk_scores": [item.get("risk_probability") for item in sessions],
        "disclaimer": DISCLAIMER,
    }