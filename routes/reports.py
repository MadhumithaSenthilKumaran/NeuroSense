import os
import uuid
from datetime import timezone
from flask import Blueprint, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from pymongo import ReturnDocument

from extensions import get_db
from services.pdf_report import build_report_pdf
from services.rag import generate_longitudinal_recommendations, generate_recommendations
from services.session_assessment import trend

reports_bp = Blueprint("reports", __name__)


def _ordinal(number):
    number = int(number)
    if 10 < number % 100 < 14:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _report_timestamp(value):
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone().isoformat()


@reports_bp.post("/final/<cycle_id>")
@jwt_required()
def generate_final_report(cycle_id):
    db = get_db()
    sessions = list(db.assessments.find({"cycle_id": cycle_id, "user_id": get_jwt_identity(), "status": "completed"}).sort("session_number", 1))
    if len(sessions) < 3:
        return jsonify(error="Complete all three sessions before generating the final report"), 400
    rows = []
    for session in sessions:
        modalities = session.get("modality_scores", {})
        rows.append({
            "session_number": session.get("session_number"),
            "session_label": _ordinal(session.get("session_number", 1)) + " session",
            "scheduled_for": session.get("scheduled_for"),
            "completed_at": _report_timestamp(session.get("completed_at")),
            "risk_probability": session.get("risk_probability"),
            "risk_class": session.get("risk_class"),
            "cognitive_score": (session.get("cognitive_result") or {}).get("overall_cognitive_score"),
            "speech_score": modalities.get("speech"),
            "clinical_score": session.get("clinical_probability", modalities.get("clinical")),
            "concern_score": session.get("clinical_concern_score", session.get("concern_score")),
            "lifestyle_score": session.get("lifestyle_score"),
            "lifestyle_probability": session.get("lifestyle_probability"),
            "modality_scores": modalities,
        })
    report_data = {
        "cycle_id": cycle_id,
        "sessions": rows,
        "trends": {key: trend([row.get(key) for row in rows]) for key in (
            "risk_probability", "cognitive_score", "speech_score",
            "clinical_score", "concern_score", "lifestyle_score",
        )},
        "recommendations": generate_longitudinal_recommendations(rows),
        "session_count": len(rows),
    }
    user = db.users.find_one({"_id": ObjectId(get_jwt_identity())}) or {}
    reports_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "reports")
    os.makedirs(reports_dir, exist_ok=True)
    output_path = os.path.join(reports_dir, f"neurosense_final_{cycle_id}_{uuid.uuid4().hex[:8]}.pdf")
    build_report_pdf(
        output_path, user,
        {"report_type": "final", "completed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)},
        {}, {}, [], f"https://neurosense.app/verify/cycle/{cycle_id}", report_data,
    )
    result = db.reports.find_one_and_update(
        {"cycle_id": cycle_id, "user_id": get_jwt_identity(), "report_type": "final"},
        {"$set": {"report_data": report_data, "pdf_path": output_path, "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)}},
        upsert=True, return_document=ReturnDocument.AFTER,
    )
    return jsonify(report_id=str(result["_id"]), report=report_data, download_url=f"/api/reports/download/{result['_id']}"), 201


@reports_bp.post("/generate/<assessment_id>")
@jwt_required()
def generate_report(assessment_id):
    db = get_db()
    user_id = get_jwt_identity()
    try:
        assessment = db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": user_id})
        if not assessment:
            return jsonify(error="Assessment not found"), 404
        if assessment.get("status") != "completed":
            return jsonify(error="Assessment is not yet completed"), 400

        user = db.users.find_one({"_id": ObjectId(user_id)})
        lifestyle = db.lifestyle_responses.find_one({"assessment_id": assessment_id}) or {}
        cognitive = assessment.get("cognitive_result") or {}
        speech_docs = list(db.speech_features.find({"assessment_id": assessment_id}))
        recommendations = assessment.get("recommendations")
        if not recommendations:
            lifestyle_answers = lifestyle.get("answers", {})
            recommendations = generate_recommendations(
                assessment.get("risk_class", "Moderate"),
                assessment.get("shap_top_features", []),
                lifestyle.get("elevated_risk_factors", []),
            )
            db.assessments.update_one(
                {"_id": ObjectId(assessment_id)},
                {"$set": {"recommendations": recommendations}},
            )
            assessment["recommendations"] = recommendations

        reports_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "reports")
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"neurosense_report_{assessment_id}_{uuid.uuid4().hex[:8]}.pdf"
        output_path = os.path.join(reports_dir, filename)

        verification_url = f"https://neurosense.app/verify/{assessment_id}"
        build_report_pdf(output_path, user or {}, assessment, lifestyle, cognitive, speech_docs, verification_url)

        # Verify file was created
        if not os.path.exists(output_path):
            return jsonify(error="Failed to create PDF file"), 500
        
        if os.path.getsize(output_path) == 0:
            return jsonify(error="Generated PDF is empty"), 500

        report_doc = {
            "assessment_id": assessment_id,
            "user_id": user_id,
            "pdf_path": output_path,
            "qr_payload": verification_url,
            "emailed_to_guardian": False,
            "recommendations": recommendations,
        }
        from models.schemas import now
        report_doc["generated_at"] = now()
        result = db.reports.insert_one(report_doc)

        return jsonify(
            report_id=str(result.inserted_id), 
            download_url=f"/api/reports/download/{result.inserted_id}",
            filename=filename,
            recommendations=recommendations,
        ), 201
    except Exception as e:
        return jsonify(error=f"Failed to generate report: {str(e)}"), 500


@reports_bp.get("/download/<report_id>")
@jwt_required()
def download_report(report_id):
    db = get_db()
    try:
        report = db.reports.find_one({"_id": ObjectId(report_id)})
        if not report:
            return jsonify(error="Report not found in database"), 404
        
        pdf_path = report.get("pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            return jsonify(error=f"Report file not found at path: {pdf_path}"), 404
        
        # Verify file has content
        if os.path.getsize(pdf_path) == 0:
            return jsonify(error="Report file is empty"), 400
            
        return send_file(
            pdf_path, 
            as_attachment=True,
            download_name=f"NeuroSense_Report_{report_id}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify(error=f"Failed to download report: {str(e)}"), 500


@reports_bp.post("/email-guardian/<report_id>")
@jwt_required()
def email_guardian(report_id):
    """
    Emails the PDF to the user's registered guardian, only if consent_share
    was checked at registration/profile time. Requires SMTP_* env vars —
    see config.py. Returns 501 if SMTP is not configured (dev default).
    """
    db = get_db()
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    report = db.reports.find_one({"_id": ObjectId(report_id), "user_id": user_id})
    if not report:
        return jsonify(error="Report not found"), 404
    if not user.get("consent_share"):
        return jsonify(error="Guardian sharing consent was not granted"), 403
    if not user.get("guardian_email"):
        return jsonify(error="No guardian email on file"), 400

    if not current_app.config["SMTP_HOST"]:
        return jsonify(error="Email sending is not configured on this server (SMTP_HOST unset)"), 501

    from services.email_service import send_report_email
    send_report_email(user["guardian_email"], report["pdf_path"], user["name"])
    db.reports.update_one({"_id": report["_id"]}, {"$set": {"emailed_to_guardian": True}})
    return jsonify(message=f"Report emailed to {user['guardian_email']}")


@reports_bp.get("/history")
@jwt_required()
def risk_history():
    """Risk score trend over time, for the dashboard's timeline chart."""
    db = get_db()
    docs = list(
        db.assessments.find(
            {"user_id": get_jwt_identity(), "status": "completed"},
            {"_id": 1, "session_number": 1, "scheduled_for": 1, "next_session_date": 1, "completed_at": 1, "risk_probability": 1, "risk_class": 1},
        ).sort("completed_at", 1)
    )
    history = [
        {
            "assessment_id": str(d["_id"]),
            "session_number": d.get("session_number"),
            "session_label": _ordinal(d.get("session_number", 1)) + " session",
            "scheduled_for": d.get("scheduled_for"),
            "next_session_date": d.get("next_session_date"),
            "date": d["completed_at"].isoformat() if d.get("completed_at") else None,
            "completed_at": _report_timestamp(d.get("completed_at")),
            "risk_probability": d.get("risk_probability"),
            "risk_class": d.get("risk_class"),
        }
        for d in docs
    ]
    final_reports = []
    for report in db.reports.find(
        {"user_id": get_jwt_identity(), "report_type": "final"},
        {"_id": 1, "cycle_id": 1, "generated_at": 1, "report_data.session_count": 1},
    ).sort("generated_at", -1):
        final_reports.append({
            "report_id": str(report["_id"]),
            "cycle_id": report.get("cycle_id"),
            "session_count": (report.get("report_data") or {}).get("session_count", 3),
            "generated_at": _report_timestamp(report.get("generated_at")),
        })
    return jsonify(history=history, final_reports=final_reports)