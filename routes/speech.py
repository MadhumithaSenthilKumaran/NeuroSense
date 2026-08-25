import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from extensions import get_db
from services.speech_features import extract_features, waveform_points
from transcription import transcribe

speech_bp = Blueprint("speech", __name__)

ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "webm", "ogg"}
TASKS = {"reading", "picture", "routine"}


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@speech_bp.post("/upload/<assessment_id>/<task>")
@jwt_required()
def upload_speech(assessment_id, task):
    if task not in TASKS:
        return jsonify(error=f"task must be one of {sorted(TASKS)}"), 400
    if "audio" not in request.files:
        return jsonify(error="No audio file in request (field name 'audio')"), 400

    file = request.files["audio"]
    if file.filename == "" or not _allowed(file.filename):
        return jsonify(error="Unsupported or missing audio file"), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{assessment_id}_{task}_{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    try:
        transcript = transcribe(save_path)
        features = extract_features(save_path, transcript=transcript)
    except Exception as e:
        current_app.logger.exception("Speech feature extraction failed")
        return jsonify(error=f"Could not process audio: {e}"), 422

    db = get_db()
    doc = {
        "assessment_id": assessment_id,
        "user_id": get_jwt_identity(),
        "task": task,
        "audio_path": save_path,
        "transcript": transcript,
        **features,
    }
    result = db.speech_features.insert_one(doc)
    db.assessments.update_one(
        {"_id": ObjectId(assessment_id)},
        {"$push": {"speech_feature_ids": str(result.inserted_id)}},
    )

    doc["_id"] = str(result.inserted_id)
    return jsonify(speech_feature=doc), 201


@speech_bp.get("/waveform/<speech_feature_id>")
@jwt_required()
def get_waveform(speech_feature_id):
    db = get_db()
    doc = db.speech_features.find_one({"_id": ObjectId(speech_feature_id)})
    if not doc:
        return jsonify(error="Not found"), 404
    points = waveform_points(doc["audio_path"])
    return jsonify(points=points)


@speech_bp.get("/tasks")
def get_tasks():
    return jsonify(tasks=[
        {
            "id": "reading",
            "title": "Read this paragraph",
            "prompt": (
                "Yesterday I went to the market with my family. We bought fruits, "
                "vegetables, and milk. Later we visited a nearby park and spent "
                "some time together."
            ),
        },
        {
            "id": "picture",
            "title": "Describe the picture",
            "prompt": "Describe what is happening in the picture shown on screen.",
            "image_url": "/assets/cookie-theft-scene.png",
        },
        {
            "id": "routine",
            "title": "Talk about your day",
            "prompt": "Talk for about one minute about your daily routine.",
            "duration_hint_s": 60,
        },
    ])