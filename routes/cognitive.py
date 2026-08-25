from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from extensions import get_db
from services.cognitive_scoring import (
    MEMORY_WORDS, ATTENTION_SEQUENCE,
    score_memory_recall, score_reaction_time, score_attention,
    score_visual_memory, score_pattern_recognition, score_orientation,
    compute_cognitive_score,
)

cognitive_bp = Blueprint("cognitive", __name__)


@cognitive_bp.get("/memory-words")
def memory_words():
    return jsonify(words=MEMORY_WORDS, display_seconds=10)


@cognitive_bp.get("/attention-sequence")
def attention_sequence():
    return jsonify(sequence=ATTENTION_SEQUENCE, question="What number came after B?")


@cognitive_bp.post("/submit/<assessment_id>")
@jwt_required()
def submit_cognitive(assessment_id):
    """
    Body:
    {
      "recalled_words": [...],
      "reaction_times_ms": [...],
      "attention_answer": "7",
      "visual_memory": {"selected": [...], "target": [...]},
      "pattern_recognition": [{"selected":.., "correct":..}, ...],
      "orientation": {"year":.., "month":.., "day":.., "city":..}
    }
    """
    data = request.get_json(force=True) or {}

    memory_result = score_memory_recall(data.get("recalled_words", []))
    reaction_result = score_reaction_time(data.get("reaction_times_ms", []))
    attention_result = score_attention(data.get("attention_answer", ""))

    vm = data.get("visual_memory", {})
    visual_memory_result = score_visual_memory(vm.get("selected"), vm.get("target"))

    pattern_result = score_pattern_recognition(data.get("pattern_recognition", []))

    now = datetime.now(timezone.utc)
    current_date = {"year": now.year, "month": now.strftime("%B"), "day": now.day}
    orientation_result = score_orientation(data.get("orientation", {}), current_date)

    sub_scores = {
        "memory_recall": memory_result["score"],
        "reaction_time": reaction_result["score"],
        "attention": attention_result["score"],
        "visual_memory": visual_memory_result["score"],
        "pattern_recognition": pattern_result["score"],
        "orientation": orientation_result["score"],
    }
    overall = compute_cognitive_score(sub_scores)

    cognitive_result = {
        "assessment_id": assessment_id,
        "user_id": get_jwt_identity(),
        "memory_recall": memory_result,
        "reaction_time": reaction_result,
        "attention": attention_result,
        "visual_memory": visual_memory_result,
        "pattern_recognition": pattern_result,
        "orientation": orientation_result,
        "overall_cognitive_score": overall,
        "created_at": now,
    }

    db = get_db()
    result = db.cognitive_tests.insert_one(cognitive_result)
    db.assessments.update_one(
        {"_id": ObjectId(assessment_id)},
        {"$set": {"cognitive_result": {**cognitive_result, "_id": str(result.inserted_id)}}},
    )

    cognitive_result["_id"] = str(result.inserted_id)
    cognitive_result["created_at"] = cognitive_result["created_at"].isoformat()
    return jsonify(cognitive_result=cognitive_result), 201