from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from extensions import get_db
from services.lifestyle_scoring import (
    LIFESTYLE_QUESTIONS, CONCERN_QUESTIONS, CONCERN_SCALE,
    score_lifestyle, score_concern, compare_lifestyle_answers,
)

lifestyle_bp = Blueprint("lifestyle", __name__)


@lifestyle_bp.get("/questions")
def get_questions():
    return jsonify(questions=LIFESTYLE_QUESTIONS)


@lifestyle_bp.get("/concern-questions")
def get_concern_questions():
    return jsonify(questions=CONCERN_QUESTIONS, scale=CONCERN_SCALE)


@lifestyle_bp.post("/submit/<assessment_id>")
@jwt_required()
def submit_lifestyle(assessment_id):
    data = request.get_json(force=True) or {}
    answers = data.get("answers", {})
    concern_answers = data.get("concern_answers", {})

    lifestyle_result = score_lifestyle(answers)
    concern_result = score_concern(concern_answers)

    db = get_db()
    assessment = db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": get_jwt_identity()})
    if not assessment:
        return jsonify(error="Assessment not found"), 404
    previous_lifestyle = None
    if assessment.get("session_number", 1) > 1:
        previous_lifestyle = db.lifestyle_responses.find_one(
            {"cycle_id": assessment.get("cycle_id"), "user_id": get_jwt_identity(), "session_number": assessment.get("session_number", 1) - 1},
            sort=[("created_at", -1)],
        )
    longitudinal = compare_lifestyle_answers(
        (previous_lifestyle or {}).get("answers", {}), answers,
    ) if previous_lifestyle else {
        "previous_lifestyle_score": None,
        "lifestyle_score_change": None,
        "lifestyle_trend": "baseline",
        "changed_answer_count": 0,
        "changed_answers": [],
    }
    doc = {
        "assessment_id": assessment_id,
        "user_id": get_jwt_identity(),
        "cycle_id": assessment.get("cycle_id"),
        "session_number": assessment.get("session_number", 1),
        "answers": answers,
        "concern_answers": concern_answers,
        **lifestyle_result,
        **concern_result,
        **longitudinal,
        "created_at": datetime.now(timezone.utc),
    }
    result = db.lifestyle_responses.insert_one(doc)

    db.assessments.update_one(
        {"_id": ObjectId(assessment_id)},
        {"$set": {
            "lifestyle_response_id": str(result.inserted_id),
            "concern_score": concern_result.get("concern_score"),
        }},
    )

    doc["_id"] = str(result.inserted_id)
    doc["created_at"] = doc["created_at"].isoformat()
    return jsonify(lifestyle_response=doc), 201