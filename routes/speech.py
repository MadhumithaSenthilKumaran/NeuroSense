import os
import re
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from werkzeug.utils import secure_filename

from extensions import get_db
from services.speech_features import extract_features, waveform_points
from transcription import transcribe

speech_bp = Blueprint("speech", __name__)

ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "webm", "ogg"}
TASKS = {"reading"}


def _content_match(transcript, expected):
    expected_words = {word for word in re.findall(r"[a-z]+", (expected or '').lower()) if len(word) > 3}
    transcript_words = set(re.findall(r"[a-z]+", (transcript or '').lower()))
    matched = expected_words & transcript_words
    return {"score": round(len(matched) / len(expected_words) * 100, 1) if expected_words else None, "matched_words": sorted(matched), "expected_word_count": len(expected_words)}


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@speech_bp.post("/upload/<assessment_id>/<task>")
@jwt_required()
def upload_speech(assessment_id, task):
    if task not in TASKS:
        return jsonify(error=f"task must be one of {sorted(TASKS)}"), 400
    try:
        assessment_object_id = ObjectId(assessment_id)
    except Exception:
        return jsonify(error="Invalid assessment id"), 400

    db = get_db()
    assessment = db.assessments.find_one({
        "_id": assessment_object_id,
        "user_id": get_jwt_identity(),
    })
    if not assessment:
        return jsonify(error="Assessment not found"), 404
    if "audio" not in request.files:
        return jsonify(error="No audio file in request (field name 'audio')"), 400

    file = request.files["audio"]
    if file.filename == "" or not _allowed(file.filename):
        return jsonify(error="Unsupported or missing audio file"), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{secure_filename(assessment_id)}_{task}_{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    try:
        transcript = transcribe(save_path)
        features = extract_features(save_path, transcript=transcript)
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        current_app.logger.exception("Speech feature extraction failed")
        return jsonify(error=f"Could not process audio: {e}"), 422

    assigned_speech = assessment.get("assigned_sets", {}).get("speech", {})
    doc = {
        "assessment_id": assessment_id,
        "user_id": get_jwt_identity(),
        "cycle_id": assessment.get("cycle_id"),
        "session_number": assessment.get("session_number", 1),
        "speech_set_id": assessment.get("assigned_sets", {}).get("speech", {}).get("id"),
        "content_match": _content_match(transcript, assigned_speech.get("paragraph")),
        "task": task,
        "audio_path": save_path,
        "transcript": transcript,
        **features,
    }
    result = db.speech_features.insert_one(doc)
    db.assessments.update_one(
        {"_id": assessment_object_id},
        {"$push": {"speech_feature_ids": str(result.inserted_id)}},
    )

    doc["_id"] = str(result.inserted_id)
    return jsonify(speech_feature=doc), 201


@speech_bp.get("/waveform/<speech_feature_id>")
@jwt_required()
def get_waveform(speech_feature_id):
    db = get_db()
    try:
        feature_id = ObjectId(speech_feature_id)
    except Exception:
        return jsonify(error="Invalid speech feature id"), 400

    doc = db.speech_features.find_one({
        "_id": feature_id,
        "user_id": get_jwt_identity(),
    })
    if not doc:
        return jsonify(error="Not found"), 404
    points = waveform_points(doc["audio_path"])
    return jsonify(points=points)


@speech_bp.get("/tasks")
def get_tasks():
    reading_prompt = "Please read the paragraph assigned to your session aloud at a comfortable pace."
    return jsonify(tasks=[
        {
            "id": "reading",
            "title": "Reading statement",
            "prompt": reading_prompt,
        },
    ])


@speech_bp.get("/session/<assessment_id>")
@jwt_required()
def get_session_speech(assessment_id):
    db = get_db()
    assessment = db.assessments.find_one({"_id": ObjectId(assessment_id), "user_id": get_jwt_identity()})
    if not assessment:
        return jsonify(error="Assessment not found"), 404
    assigned = assessment.get("assigned_sets", {}).get("speech", {})
    return jsonify(speech_set=assigned, analyze=["pitch_hz", "pause_duration_s", "pause_rate", "speech_rate_wpm"])