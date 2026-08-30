import os
import uuid
from flask import Blueprint, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from extensions import get_db
from services.pdf_report import build_report_pdf

reports_bp = Blueprint("reports", __name__)


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
        }
        from models.schemas import now
        report_doc["generated_at"] = now()
        result = db.reports.insert_one(report_doc)

        return jsonify(
            report_id=str(result.inserted_id), 
            download_url=f"/api/reports/download/{result.inserted_id}",
            filename=filename
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
            {"_id": 1, "completed_at": 1, "risk_probability": 1, "risk_class": 1},
        ).sort("completed_at", 1)
    )
    history = [
        {
            "assessment_id": str(d["_id"]),
            "date": d["completed_at"].isoformat() if d.get("completed_at") else None,
            "risk_probability": d.get("risk_probability"),
            "risk_class": d.get("risk_class"),
        }
        for d in docs
    ]
    return jsonify(history=history)