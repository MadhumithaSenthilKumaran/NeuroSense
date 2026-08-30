import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt,
)

from extensions import get_db
from models.schemas import new_user_doc
from services.auth_service import hash_password, verify_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(force=True) or {}
    required = ["name", "email", "password"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify(error=f"Missing fields: {', '.join(missing)}"), 400

    db = get_db()
    if db.users.find_one({"email": data["email"].lower().strip()}):
        return jsonify(error="An account with this email already exists"), 409

    doc = new_user_doc(
        name=data["name"],
        email=data["email"],
        password_hash=hash_password(data["password"]),
        age=data.get("age"),
        gender=data.get("gender"),
        phone=data.get("phone"),
        education=data.get("education"),
        occupation=data.get("occupation"),
        guardian_email=data.get("guardian_email"),
        guardian_phone=data.get("guardian_phone"),
        consent_share=data.get("consent_share", False),
    )
    result = db.users.insert_one(doc)
    user_id = str(result.inserted_id)
    token = create_access_token(identity=user_id, additional_claims={"role": "user"})
    user_payload = {k: doc[k] for k in [
        "name", "email", "age", "gender", "phone",
        "education", "occupation", "guardian_email", "guardian_phone", "consent_share"
    ] if k in doc}
    user_payload["id"] = user_id
    return jsonify(access_token=token, user=user_payload), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""

    db = get_db()
    user = db.users.find_one({"email": email})
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify(error="Invalid email or password"), 401

    token = create_access_token(
        identity=str(user["_id"]), additional_claims={"role": user.get("role", "user")}
    )
    safe_user = {k: v for k, v in user.items() if k not in {"_id", "password_hash"}}
    safe_user["id"] = str(user["_id"])
    return jsonify(access_token=token, user=safe_user)


@auth_bp.post("/forgot-password")
def forgot_password():
    """
    Issues a one-time reset token. Actual delivery (email/SMS) requires SMTP
    credentials — see config.py. In LIGHTWEIGHT_MODE the token is returned
    directly in the response for local development/testing only.
    """
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").lower().strip()
    db = get_db()
    user = db.users.find_one({"email": email})
    if not user:
        # Do not reveal whether the account exists.
        return jsonify(message="If that account exists, a reset link has been sent."), 200

    reset_token = uuid.uuid4().hex
    db.users.update_one({"_id": user["_id"]}, {"$set": {"reset_token": reset_token}})

    from flask import current_app
    if current_app.config["LIGHTWEIGHT_MODE"]:
        return jsonify(message="Reset token generated (dev mode).", reset_token=reset_token), 200
    # TODO: send via SMTP using services/email_service.py in production mode.
    return jsonify(message="If that account exists, a reset link has been sent."), 200


@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json(force=True) or {}
    token = data.get("reset_token")
    new_password = data.get("new_password")
    if not token or not new_password:
        return jsonify(error="reset_token and new_password are required"), 400

    db = get_db()
    user = db.users.find_one({"reset_token": token})
    if not user:
        return jsonify(error="Invalid or expired reset token"), 400

    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": hash_password(new_password)}, "$unset": {"reset_token": ""}},
    )
    return jsonify(message="Password updated successfully.")


@auth_bp.get("/me")
@jwt_required()
def me():
    from bson import ObjectId
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(get_jwt_identity())}, {"password_hash": 0})
    if not user:
        return jsonify(error="User not found"), 404
    user["id"] = str(user.pop("_id"))
    return jsonify(user=user)


@auth_bp.put("/me")
@jwt_required()
def update_me():
    from bson import ObjectId
    data = request.get_json(force=True) or {}
    allowed = {
        "name", "age", "gender", "phone", "education", "occupation",
        "guardian_email", "guardian_phone", "consent_share",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    db = get_db()
    db.users.update_one({"_id": ObjectId(get_jwt_identity())}, {"$set": updates})
    return jsonify(message="Profile updated.")