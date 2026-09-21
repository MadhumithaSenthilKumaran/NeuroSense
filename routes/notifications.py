from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import get_db
from services.notification_service import is_valid_email, send_assessment_notification


notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.post("/preferences")
@jwt_required()
def update_preferences():
    data = request.get_json(silent=True) or {}
    updates = {}
    for field in ("email_notifications",):
        if field in data and isinstance(data[field], bool):
            updates[field] = data[field]
    if not updates:
        return jsonify(error="No valid notification preferences supplied"), 400
    get_db().users.update_one({"_id": ObjectId(get_jwt_identity())}, {"$set": updates})
    return jsonify(message="Notification preferences updated.")


@notifications_bp.post("/test")
@jwt_required()
def test_notification():
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(get_jwt_identity())}) or {}
    if not is_valid_email(user.get("email")):
        return jsonify(error="Your account email is invalid"), 400
    statuses = send_assessment_notification(user)
    statuses["attempted_at"] = datetime.now(timezone.utc).isoformat()
    return jsonify(statuses=statuses)