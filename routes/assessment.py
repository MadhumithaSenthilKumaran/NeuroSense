from datetime import datetime, timezone
import os
import uuid
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from extensions import get_db
from services.fusion import fuse
from services.feature_mapping import map_questionnaire_to_clinical_features
from services.linguistic_features import extract_linguistic_features
from services.rag import generate_recommendations, generate_longitudinal_recommendations
from services.session_assessment import STORY_BANK, assign_sets, build_cycle_schedule, trend
from services.lifestyle_scoring import score_lifestyle
from services.email_service import send_session_reminder
from services.pdf_report import build_report_pdf
from services.notification_service import send_assessment_notification, send_session_day_notification

assessment_bp = Blueprint("assessment", __name__)
logger = logging.getLogger(__name__)


@assessment_bp.post("/start")
@jwt_required()
def start_assessment(cycle_id_override=None, session_number_override=None):
    from models.schemas import new_assessment_doc
    db = get_db()
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    now = datetime.now(timezone.utc)
    cycle_id = cycle_id_override or data.get("cycle_id")
    cycle = None
    session_number = int(session_number_override or data.get("session_number", 1))
    if session_number not in (1, 2, 3):
        return jsonify(error="session_number must be 1, 2, or 3"), 400

    if cycle_id:
        cycle = db.assessment_cycles.find_one({"cycle_id": cycle_id, "user_id": user_id})
        if not cycle:
            return jsonify(error="Assessment cycle not found"), 404
        previous = list(db.assessments.find({"cycle_id": cycle_id, "user_id": user_id}))
        if any(item.get("session_number") == session_number for item in previous):
            return jsonify(error="This session has already been started"), 409
        started_at = cycle["started_at"]
    else:
        cycle_id = __import__("uuid").uuid4().hex
        started_at = now
        cycle_schedule = build_cycle_schedule(started_at)
        db.assessment_cycles.insert_one({
            "cycle_id": cycle_id, "user_id": user_id, "started_at": started_at,
            "schedule": cycle_schedule, "status": "in_progress",
        })
        cycle = {"schedule": cycle_schedule, "started_at": started_at}

    schedule = next(item for item in cycle.get("schedule", build_cycle_schedule(started_at)) if item["session_number"] == session_number)
    if cycle_id and session_number > 1:
        today = now.astimezone().date().isoformat()
        if today < schedule["scheduled_for"]:
            return jsonify(error=f"Session {session_number} is available on {schedule['scheduled_for']}"), 403
        if today > schedule["scheduled_for"]:
            return jsonify(error=f"Session {session_number} was scheduled for {schedule['scheduled_for']} and is no longer available"), 403
        if today == schedule["scheduled_for"]:
            try:
                user = db.users.find_one({"_id": ObjectId(user_id)}) or {}
                reminder = db.notifications.find_one({
                    "user_id": user_id, "cycle_id": cycle_id, "session_number": session_number,
                    "session_day_email_sent": True,
                })
                if not reminder:
                    email_status = send_session_day_notification(user, session_number, schedule["scheduled_for"])
                    db.notifications.update_one(
                        {"user_id": user_id, "cycle_id": cycle_id, "session_number": session_number},
                        {"$set": {"session_day_email_sent": email_status == "sent", "session_day_email_status": email_status, "created_at": now}},
                        upsert=True,
                    )
            except Exception as error:
                logger.error("Session-day email notification handling failed: %s", error)

    prior = list(db.assessments.find({"user_id": user_id}, {"cycle_id": 1, "session_number": 1, "assigned_sets": 1}).sort("session_number", 1))
    used = {key: [item.get("assigned_sets", {}).get(key, {}).get("id") for item in prior]
            for key in ("story", "memory", "speech")}
    used["speech"] = [speech_id for item in prior for speech_id in (
        [item.get("assigned_sets", {}).get("speech", {}).get("id")]
        + [option.get("id") for option in item.get("assigned_sets", {}).get("speech", {}).get("options", [])]
    ) if speech_id]

    current_cycle_prior = [item for item in prior if item.get("cycle_id") == cycle_id]
    previous_assessment = next(
        (item for item in current_cycle_prior if item.get("session_number") == session_number - 1),
        None,
    )
    if session_number > 1 and not previous_assessment:
        return jsonify(error=f"Complete Session {session_number - 1} before starting Session {session_number}"), 409
    previous_story_id = (previous_assessment or {}).get("assigned_sets", {}).get("story", {}).get("id")
    assigned_sets = assign_sets(
        used["story"],
        used["memory"],
        used["speech"],
        preferred_story_id=previous_story_id,
    )
    if session_number > 1:
        previous_story = (previous_assessment or {}).get("assigned_sets", {}).get("story")
        if previous_story:
            assigned_sets["story_questions"] = previous_story.get("questions", []) or next(
                (item.get("questions", []) for item in STORY_BANK
                 if item.get("id") == previous_story.get("id")),
                [],
            )
    doc = new_assessment_doc(user_id, session_number, cycle_id, schedule["scheduled_for"], assigned_sets)
    doc["cycle_schedule"] = cycle.get("schedule", build_cycle_schedule(started_at))
    result = db.assessments.insert_one(doc)
    db.assessment_cycles.update_one(
        {"cycle_id": cycle_id},
        {"$set": {f"schedule.{session_number - 1}.status": "started"}},
    )
    doc["_id"] = str(result.inserted_id)
    doc["created_at"] = doc["created_at"].isoformat()
    return jsonify(assessment=doc), 201


@assessment_bp.post("/<assessment_id>/next")
@jwt_required()
def start_next_session(assessment_id):
    db = get_db()
    current = db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": get_jwt_identity()})
    if not current:
        return jsonify(error="Assessment not found"), 404
    next_number = int(current.get("session_number", 1)) + 1
    if next_number > 3:
        return jsonify(error="The three-session cycle is complete"), 400
    return start_assessment(current.get("cycle_id"), next_number)


@assessment_bp.get("/cycle/<cycle_id>")
@jwt_required()
def get_cycle(cycle_id):
    db = get_db()
    cycle = db.assessment_cycles.find_one({"cycle_id": cycle_id, "user_id": get_jwt_identity()}, {"_id": 0})
    if not cycle:
        return jsonify(error="Assessment cycle not found"), 404
    sessions = list(db.assessments.find({"cycle_id": cycle_id}, {"_id": 1, "session_number": 1, "status": 1, "scheduled_for": 1, "risk_class": 1, "modality_scores": 1}).sort("session_number", 1))
    for session in sessions:
        session["assessment_id"] = str(session.pop("_id"))
    return jsonify(cycle=cycle, sessions=sessions)


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
    assessment = db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": get_jwt_identity()})
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
    answers = lifestyle_doc.get("answers", {})
    try:
        lifestyle_stress_score = float(answers.get("stress_level")) * 10
    except (TypeError, ValueError):
        lifestyle_stress_score = None
    response_consistency_score = (cognitive_result or {}).get("response_consistency_score")

    fusion_result = fuse(
        clinical_features, speech_linguistic, cognitive_overall, concern_score,
        lifestyle_stress_score, response_consistency_score,
    )

    recommendations = generate_recommendations(
        fusion_result["risk_class"],
        fusion_result["shap_top_features"],
        lifestyle_doc.get("elevated_risk_factors", []),
    )

    now = datetime.now(timezone.utc)
    lifestyle_score = lifestyle_doc.get("lifestyle_score")
    if lifestyle_score is None:
        lifestyle_score = score_lifestyle(lifestyle_doc.get("answers", {})).get("lifestyle_score")
    lifestyle_probability = round(1 - (float(lifestyle_score) / 100), 4) if lifestyle_score is not None else None
    cycle = db.assessment_cycles.find_one({"cycle_id": assessment.get("cycle_id"), "user_id": get_jwt_identity()}) or {}
    cycle_schedule = build_cycle_schedule(cycle.get("started_at") or assessment.get("created_at") or now)
    next_schedule = next(
        (item for item in cycle_schedule if item["session_number"] == assessment.get("session_number", 1) + 1),
        None,
    )
    schedule_message = (
        f"Your next assessment is scheduled for {next_schedule['scheduled_for']}. "
        "Please complete it on that date. No appointment time is required."
        if next_schedule else "This is the final assessment in the one-week cycle."
    )
    update = {
        "status": "completed",
        "completed_at": now,
        "fused_features": clinical_features,
        "lifestyle_score": lifestyle_score,
        "lifestyle_probability": lifestyle_probability,
        "previous_lifestyle_score": lifestyle_doc.get("previous_lifestyle_score"),
        "lifestyle_score_change": lifestyle_doc.get("lifestyle_score_change"),
        "lifestyle_trend": lifestyle_doc.get("lifestyle_trend"),
        "clinical_probability": fusion_result["modality_scores"].get("clinical"),
        "clinical_concern_score": concern_score,
        "lifestyle_stress_score": lifestyle_stress_score,
        "response_consistency_score": response_consistency_score,
        "risk_probability": fusion_result["risk_probability"],
        "risk_class": fusion_result["risk_class"],
        "modality_scores": fusion_result["modality_scores"],
        "shap_top_features": fusion_result["shap_top_features"],
        "used_modalities": fusion_result["used_modalities"],
        "recommendations": recommendations,
        "next_assessment_suggestion": schedule_message,
        "next_session_date": next_schedule["scheduled_for"] if next_schedule else None,
        "session_label": f"Session {assessment.get('session_number', 1)}",
        "cycle_schedule": cycle_schedule,
    }
    db.assessments.update_one({"_id": ObjectId(assessment_id)}, {"$set": update})
    session_report = {
        "assessment_id": assessment_id,
        "cycle_id": assessment.get("cycle_id"),
        "user_id": get_jwt_identity(),
        "report_type": "session",
        "session_number": assessment.get("session_number", 1),
        "report_data": {
            **update,
            "lifestyle_response": lifestyle_doc,
            "clinical_concern_score": concern_score,
            "cognitive_result": cognitive_result,
            "speech_features": speech_docs,
        },
        "generated_at": now,
    }
    db.reports.update_one(
        {"assessment_id": assessment_id, "report_type": "session"},
        {"$set": session_report},
        upsert=True,
    )

    if next_schedule:
        user = db.users.find_one({"_id": ObjectId(get_jwt_identity())}) or {}
        message = (
            f"Session {assessment.get('session_number', 1) + 1} is scheduled for "
            f"{next_schedule['scheduled_for']}. It will be available only on that date."
        )
        db.notifications.update_one(
            {"user_id": get_jwt_identity(), "cycle_id": assessment.get("cycle_id"), "session_number": assessment.get("session_number", 1) + 1},
            {"$set": {"message": message, "scheduled_for": next_schedule["scheduled_for"], "read": False, "created_at": now}},
            upsert=True,
        )
        if user.get("email") and user.get("email_notifications", True) and current_app.config.get("SMTP_HOST"):
            try:
                send_session_reminder(user["email"], user.get("name", "there"), assessment.get("session_number", 1) + 1, next_schedule["scheduled_for"])
                db.notifications.update_one(
                    {"user_id": get_jwt_identity(), "cycle_id": assessment.get("cycle_id"), "session_number": assessment.get("session_number", 1) + 1},
                    {"$set": {"emailed": True}},
                )
            except Exception:
                pass

    if assessment.get("session_number") == 3:
        completed = list(db.assessments.find(
            {"cycle_id": assessment.get("cycle_id"), "user_id": get_jwt_identity(), "status": "completed"}
        ).sort("session_number", 1))
        if len(completed) == 3:
            rows = []
            for item in completed:
                modalities = item.get("modality_scores", {})
                rows.append({
                    "session_number": item.get("session_number"),
                    "risk_probability": item.get("risk_probability"),
                    "risk_class": item.get("risk_class"),
                    "cognitive_score": (item.get("cognitive_result") or {}).get("overall_cognitive_score"),
                    "speech_score": modalities.get("speech"),
                    "clinical_score": modalities.get("clinical"),
                    "concern_score": item.get("concern_score"),
                    "lifestyle_score": item.get("lifestyle_score"),
                    "lifestyle_probability": item.get("lifestyle_probability"),
                    "modality_scores": modalities,
                })
                final_data = {
                "cycle_id": assessment.get("cycle_id"),
                    "report_type": "final",
                    "session_count": len(rows),
                "sessions": rows,
                "trends": {key: trend([row.get(key) for row in rows]) for key in ("risk_probability", "cognitive_score", "speech_score", "clinical_score", "concern_score")},
                "recommendations": generate_longitudinal_recommendations(rows),
            }
            db.reports.update_one(
                {"cycle_id": assessment.get("cycle_id"), "user_id": get_jwt_identity(), "report_type": "final"},
                {"$set": {"report_data": final_data, "generated_at": now}},
                upsert=True,
            )
            user = db.users.find_one({"_id": ObjectId(get_jwt_identity())}) or {}
            reports_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "reports")
            os.makedirs(reports_dir, exist_ok=True)
            output_path = os.path.join(reports_dir, f"neurosense_final_{assessment.get('cycle_id')}_{uuid.uuid4().hex[:8]}.pdf")
            build_report_pdf(
                output_path, user, {"report_type": "final", "completed_at": now},
                {}, {}, [], f"https://neurosense.app/verify/cycle/{assessment.get('cycle_id')}", final_data,
            )
            db.reports.update_one(
                {"cycle_id": assessment.get("cycle_id"), "user_id": get_jwt_identity(), "report_type": "final"},
                {"$set": {"pdf_path": output_path}},
            )

    # Report persistence is complete before notifications are attempted. Each
    # channel is isolated by the service so delivery cannot fail finalization.
    user = db.users.find_one({"_id": ObjectId(get_jwt_identity())}) or {}
    try:
        notification_status = send_assessment_notification(user)
    except Exception as error:
        logger.error("Assessment notification dispatch failed: %s", error)
        notification_status = {"email_notification_status": "failed"}
    notification_status["notification_attempted_at"] = datetime.now(timezone.utc)
    try:
        db.assessments.update_one({"_id": ObjectId(assessment_id)}, {"$set": notification_status})
        db.reports.update_one(
            {"assessment_id": assessment_id, "report_type": "session"},
            {"$set": notification_status},
        )
    except Exception as error:
        logger.error("Unable to store assessment notification status: %s", error)

    result_doc = {**assessment, **update}
    result_doc["_id"] = str(result_doc["_id"])
    result_doc["completed_at"] = now.isoformat()
    result_doc.update({key: value for key, value in notification_status.items() if key != "notification_attempted_at"})
    if isinstance(result_doc.get("created_at"), datetime):
        result_doc["created_at"] = result_doc["created_at"].isoformat()

    return jsonify(assessment=result_doc)