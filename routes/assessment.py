from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from extensions import get_db
from services.fusion import fuse
from services.feature_mapping import map_questionnaire_to_clinical_features
from services.linguistic_features import extract_linguistic_features
from services.rag import generate_recommendations

assessment_bp = Blueprint("assessment", __name__)


@assessment_bp.post("/start")
@jwt_required()
def start_assessment():
    from models.schemas import new_assessment_doc
    db = get_db()
    doc = new_assessment_doc(get_jwt_identity())
    result = db.assessments.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["created_at"] = doc["created_at"].isoformat()
    return jsonify(assessment=doc), 201


@assessment_bp.get("/<assessment_id>")
@jwt_required()
def get_assessment(assessment_id):
    db = get_db()
    doc = db.assessments.find_one({"_id": ObjectId(assessment_id)})
    if not doc:
        return jsonify(error="Not found"), 404
    doc["_id"] = str(doc["_id"])
    return jsonify(assessment=doc)


@assessment_bp.get("/history/mine")
@jwt_required()
def my_history():
    db = get_db()
    docs = list(db.assessments.find({"user_id": get_jwt_identity(), "status": "completed"})
                .sort("completed_at", -1))
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify(assessments=docs)


@assessment_bp.post("/<assessment_id>/finalize")
@jwt_required()
def finalize_assessment(assessment_id):
    """
    Pulls together all four modules already submitted for this assessment,
    runs feature fusion (clinical model + speech model + cognitive +
    concern), generates recommendations, and marks the assessment complete.
    """
    db = get_db()
    assessment = db.assessments.find_one({"_id": ObjectId(assessment_id)})
    if not assessment:
        return jsonify(error="Assessment not found"), 404

    lifestyle_doc = None
    if assessment.get("lifestyle_response_id"):
        lifestyle_doc = db.lifestyle_responses.find_one(
            {"_id": ObjectId(assessment["lifestyle_response_id"])}
        )
    if not lifestyle_doc:
        return jsonify(error="Lifestyle questionnaire (Module 3) must be completed first"), 400

    clinical_features = map_questionnaire_to_clinical_features(
        lifestyle_doc.get("answers", {}), lifestyle_doc.get("concern_answers", {})
    )

    # Speech: use the most recent transcript-bearing speech_features doc, if any
    speech_docs = list(db.speech_features.find({"assessment_id": assessment_id}))
    speech_linguistic = None
    for sd in speech_docs:
        if sd.get("transcript"):
            speech_linguistic = extract_linguistic_features(sd["transcript"], sd.get("duration_s"))
            break

    cognitive_result = assessment.get("cognitive_result")
    cognitive_overall = cognitive_result.get("overall_cognitive_score") if cognitive_result else None
    concern_score = assessment.get("concern_score")

    fusion_result = fuse(clinical_features, speech_linguistic, cognitive_overall, concern_score)

    recommendations = generate_recommendations(
        fusion_result["risk_class"],
        fusion_result["shap_top_features"],
        lifestyle_doc.get("elevated_risk_factors", []),
    )

    now = datetime.now(timezone.utc)
    update = {
        "status": "completed",
        "completed_at": now,
        "fused_features": clinical_features,
        "risk_probability": fusion_result["risk_probability"],
        "risk_class": fusion_result["risk_class"],
        "modality_scores": fusion_result["modality_scores"],
        "shap_top_features": fusion_result["shap_top_features"],
        "used_modalities": fusion_result["used_modalities"],
        "recommendations": recommendations,
    }
    db.assessments.update_one({"_id": ObjectId(assessment_id)}, {"$set": update})

    result_doc = {**assessment, **update}
    result_doc["_id"] = str(result_doc["_id"])
    result_doc["completed_at"] = now.isoformat()
    if isinstance(result_doc.get("created_at"), datetime):
        result_doc["created_at"] = result_doc["created_at"].isoformat()

    return jsonify(assessment=result_doc)