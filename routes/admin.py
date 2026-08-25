import os
import json
from functools import wraps
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from bson import ObjectId

from extensions import get_db

admin_bp = Blueprint("admin", __name__)


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify(error="Admin access required"), 403
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.get("/dashboard")
@admin_required
def dashboard():
    db = get_db()
    total_users = db.users.count_documents({"role": "user"})
    total_assessments = db.assessments.count_documents({})
    completed = db.assessments.count_documents({"status": "completed"})
    risk_breakdown = list(db.assessments.aggregate([
        {"$match": {"status": "completed"}},
        {"$group": {"_id": "$risk_class", "count": {"$sum": 1}}},
    ]))
    return jsonify(
        total_users=total_users,
        total_assessments=total_assessments,
        completed_assessments=completed,
        risk_breakdown={r["_id"]: r["count"] for r in risk_breakdown if r["_id"]},
    )


@admin_bp.get("/users")
@admin_required
def list_users():
    db = get_db()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 25))
    users = list(
        db.users.find({}, {"password_hash": 0})
        .skip((page - 1) * limit).limit(limit)
    )
    for u in users:
        u["_id"] = str(u["_id"])
    total = db.users.count_documents({})
    return jsonify(users=users, total=total, page=page, limit=limit)


@admin_bp.get("/assessments")
@admin_required
def list_assessments():
    db = get_db()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 25))
    status_filter = request.args.get("status")
    query = {"status": status_filter} if status_filter else {}
    docs = list(
        db.assessments.find(query).sort("created_at", -1)
        .skip((page - 1) * limit).limit(limit)
    )
    for d in docs:
        d["_id"] = str(d["_id"])
    total = db.assessments.count_documents(query)
    return jsonify(assessments=docs, total=total, page=page, limit=limit)


@admin_bp.get("/model-statistics")
@admin_required
def model_statistics():
    """Surfaces the real offline evaluation metrics saved during training."""
    artifact_dir = current_app.config["MODEL_DIR"]
    stats = {}
    for name, filename in [
        ("clinical_model", "clinical_metrics.json"),
        ("speech_model", "speech_metrics.json"),
    ]:
        path = os.path.join(artifact_dir, filename)
        if os.path.exists(path):
            with open(path) as f:
                stats[name] = json.load(f)
        else:
            stats[name] = {"status": "not trained — run the training script in ml/"}
    return jsonify(model_statistics=stats)


@admin_bp.get("/feedback")
@admin_required
def list_feedback():
    db = get_db()
    docs = list(db.feedback.find().sort("created_at", -1).limit(100))
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify(feedback=docs)


@admin_bp.post("/feedback")
@jwt_required()
def submit_feedback():
    """Any logged-in user can submit feedback (not admin-only)."""
    data = request.get_json(force=True) or {}
    from models.schemas import now
    db = get_db()
    doc = {
        "user_id": get_jwt_identity(),
        "assessment_id": data.get("assessment_id"),
        "rating": data.get("rating"),
        "comments": data.get("comments"),
        "created_at": now(),
    }
    db.feedback.insert_one(doc)
    return jsonify(message="Feedback recorded — thank you."), 201


@admin_bp.get("/questionnaire")
@admin_required
def get_questionnaire_editor():
    """Returns the live questionnaire definitions so an admin can review/edit them."""
    from services.lifestyle_scoring import LIFESTYLE_QUESTIONS, CONCERN_QUESTIONS
    return jsonify(lifestyle_questions=LIFESTYLE_QUESTIONS, concern_questions=CONCERN_QUESTIONS)


@admin_bp.post("/dataset-upload")
@admin_required
def upload_dataset():
    """
    Accepts a new training CSV for future retraining. Stored under
    ml/data/uploaded/ — retraining itself is triggered separately via
    /api/admin/retrain (kept as two steps deliberately, so an admin can
    review the uploaded file before kicking off a training run).
    """
    if "file" not in request.files:
        return jsonify(error="No file provided (field name 'file')"), 400
    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify(error="Only .csv files are accepted"), 400

    upload_dir = os.path.join(os.path.dirname(current_app.config["MODEL_DIR"]), "data", "uploaded")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, file.filename)
    file.save(save_path)
    return jsonify(message="Dataset uploaded.", path=save_path), 201


@admin_bp.post("/retrain")
@admin_required
def retrain():
    """
    Triggers a synchronous retrain of the clinical model using
    ml/train_clinical_model.py against whatever CSV is currently at
    ml/data/alzheimers_disease_data.csv. For a real deployment this should
    be an async job (Celery/RQ) rather than run inline on the request —
    kept synchronous here for scaffold simplicity.
    """
    try:
        from ml.train_clinical_model import train
        _model, _scaler, _features, metrics = train()
    except Exception as e:
        current_app.logger.exception("Retrain failed")
        return jsonify(error=f"Retrain failed: {e}"), 500

    # Model cache in services/ml_model.py must be cleared so the next
    # prediction picks up the freshly retrained artifacts.
    from services import ml_model
    ml_model._cache.clear()

    return jsonify(message="Model retrained.", metrics=metrics)