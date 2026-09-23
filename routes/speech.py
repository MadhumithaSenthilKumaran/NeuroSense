import os
import re
import uuid
import re
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from werkzeug.utils import secure_filename

from extensions import get_db
from services.speech_features import extract_features, waveform_points
from services.linguistic_features import extract_linguistic_features
from services.session_assessment import SPEECH_BANK
from transcription import transcribe

speech_bp = Blueprint("speech", __name__)

ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "webm", "ogg"}
TASK_PATTERN = re.compile(r"reading(?:_\d+)?$")


def _content_match(transcript, expected):
    expected_words = {word for word in re.findall(r"[a-z]+", (expected or '').lower()) if len(word) > 3}
    transcript_words = set(re.findall(r"[a-z]+", (transcript or '').lower()))
    matched = expected_words & transcript_words
    return {"score": round(len(matched) / len(expected_words) * 100, 1) if expected_words else None, "matched_words": sorted(matched), "expected_word_count": len(expected_words)}


def _is_low_quality_transcript(transcript):
    if not transcript or not transcript.strip():
        return True
    words = re.findall(r"[A-Za-z']+", transcript.lower())
    if not words:
        return True
    if len(words) < 3:
        return True
    unique_words = len(set(words))
    if len(words) <= 8 and unique_words <= 2:
        return True
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    top_word_count = max(counts.values()) if counts else 0
    if len(words) <= 15 and top_word_count / len(words) > 0.75 and unique_words <= 3:
        return True
    return False


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@speech_bp.post("/upload/<assessment_id>/<task>")
@jwt_required()
def upload_speech(assessment_id, task):
    if not TASK_PATTERN.fullmatch(task):
        return jsonify(error="task must be a reading passage id"), 400
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
        current_app.logger.info("Speech transcript for %s: %r", filename, transcript)
        if transcript is None:
            if os.path.exists(save_path):
                os.remove(save_path)
            return jsonify(error="No speech transcript could be detected. Please record clearly and avoid silence or background noise."), 422
        if _is_low_quality_transcript(transcript):
            if os.path.exists(save_path):
                os.remove(save_path)
            return jsonify(error="Speech was too short or unclear. Please record the passage clearly and try again."), 422
        features = extract_features(save_path, transcript=transcript)
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        current_app.logger.exception("Speech feature extraction failed")
        return jsonify(error=f"Could not process audio: {e}"), 422

    assigned_speech = assessment.get("assigned_sets", {}).get("speech", {})
    speech_options = assigned_speech.get("options", [])
    option_index = 0 if task == "reading" else int(task.rsplit("_", 1)[1]) - 1
    selected_speech = speech_options[option_index] if option_index < len(speech_options) else assigned_speech
    content_match = _content_match(transcript, selected_speech.get("paragraph"))
    expected_word_count = content_match["expected_word_count"]
    reading_accuracy = content_match["score"] if content_match["score"] is not None else 0.0
    linguistic_features = extract_linguistic_features(transcript, features.get("duration_s")) or {
        "filler_count": 0,
        "token_count": 0,
        "type_count": 0,
        "type_token_ratio": 0.0,
        "ma_ttr": 0.0,
        "brunets_index": 0.0,
        "content_density": 0.0,
        "repetitions": 0,
        "sentence_count": 0,
        "average_words_per_sentence": 0.0,
        "total_seconds": features.get("duration_s", 0.0),
    }
    doc = {
        "assessment_id": assessment_id,
        "user_id": get_jwt_identity(),
        "cycle_id": assessment.get("cycle_id"),
        "session_number": assessment.get("session_number", 1),
        "speech_set_id": selected_speech.get("id"),
        "content_match": content_match,
        "reading_accuracy": reading_accuracy,
        "accuracy_rate": reading_accuracy,
        "transcript_word_count": linguistic_features["token_count"],
        "expected_word_count": expected_word_count,
        "speech_linguistic_features": linguistic_features,
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
    return jsonify(tasks=[
        {"id": "reading" if index == 0 else f"reading_{index + 1}", "title": item.get("title", f"Passage {index + 1}"), "prompt": item["paragraph"]}
        for index, item in enumerate(SPEECH_BANK)
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