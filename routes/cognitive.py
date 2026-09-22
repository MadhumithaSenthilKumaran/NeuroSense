from datetime import datetime, timezone
import os
import tempfile
import json
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from extensions import get_db
from services.cognitive_scoring import (
    MEMORY_WORDS, ATTENTION_SEQUENCE, score_memory_recall, score_attention,
    score_visual_memory, score_pattern_recognition, score_orientation,
    score_story_recall, score_game_results, compute_cognitive_score,
    cognitive_breakdown,
)
from services.praxis_analysis import analyze_praxis_video
import numpy as np

cognitive_bp = Blueprint('cognitive', __name__)
PRAXIS_WORKERS = ThreadPoolExecutor(max_workers=2, thread_name_prefix='praxis-analysis')

@cognitive_bp.post('/praxis/analyze/<assessment_id>')
@jwt_required()
def analyze_praxis(assessment_id):
    assessment = get_db().assessments.find_one({'_id': ObjectId(assessment_id), 'user_id': get_jwt_identity()})
    if not assessment:
        return jsonify(error='Assessment not found'), 404
    upload = request.files.get('video')
    if not upload:
        return jsonify(error='Praxis video is required'), 400
    numbers = request.form.getlist('prompted_numbers', type=int)
    if len(numbers) != 3 or any(number < 1 or number > 10 for number in numbers):
        return jsonify(error='Exactly three prompted numbers from 1 to 10 are required'), 400
    temporary_path = None
    try:
        capture_windows = json.loads(request.form.get('capture_windows', '[]'))
        if not isinstance(capture_windows, list) or len(capture_windows) != 3:
            return jsonify(error='Three accepted capture windows are required'), 400
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temporary:
            upload.save(temporary.name)
            temporary_path = temporary.name
        trials = PRAXIS_WORKERS.submit(
            analyze_praxis_video, temporary_path, numbers, assessment_id,
            float(request.form.get('gesture_start_seconds', 11.0)),
            capture_windows,
        ).result()
        return jsonify(praxis_trials=trials), 201
    except Exception as error:
        return jsonify(error=f'Praxis video analysis failed: {error}'), 422
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass

@cognitive_bp.get('/memory-words')
def memory_words():
    return jsonify(words=MEMORY_WORDS, display_seconds=10)

@cognitive_bp.get('/attention-sequence')
def attention_sequence():
    return jsonify(sequence=ATTENTION_SEQUENCE, question='What number came after B?')

@cognitive_bp.get('/session/<assessment_id>')
@jwt_required()
def cognitive_session(assessment_id):
    assessment = get_db().assessments.find_one({'_id': ObjectId(assessment_id), 'user_id': get_jwt_identity()})
    if not assessment:
        return jsonify(error='Assessment not found'), 404
    assigned = assessment.get('assigned_sets', {})
    return jsonify(story=assigned.get('story'), story_questions=assigned.get('story_questions', []), memory=assigned.get('memory'), session_number=assessment.get('session_number', 1), tests=assessment.get('tests', []))

@cognitive_bp.post('/submit/<assessment_id>')
@jwt_required()
def submit_cognitive(assessment_id):
    data = request.get_json(force=True) or {}
    db = get_db()
    assessment = db.assessments.find_one({'_id': ObjectId(assessment_id), 'user_id': get_jwt_identity()})
    if not assessment:
        return jsonify(error='Assessment not found'), 404
    memory_words = assessment.get('assigned_sets', {}).get('memory', {}).get('words') or MEMORY_WORDS
    memory_result = score_memory_recall(data.get('recalled_words', []), memory_words)
    story_questions = assessment.get('assigned_sets', {}).get('story_questions', [])
    story_result = score_story_recall(data.get('story_answers', []), story_questions)
    game_result = score_game_results(data.get('game_results', {}))
    attention_result = score_attention(data.get('attention_answer', ''))
    visual = data.get('visual_memory', {})
    visual_result = score_visual_memory(visual.get('selected'), visual.get('target'))
    pattern_result = score_pattern_recognition(data.get('pattern_recognition', []))
    now = datetime.now(timezone.utc)
    current_date = {'year': now.year, 'month': now.strftime('%B'), 'day': now.day}
    orientation_result = score_orientation(data.get('orientation', {}), current_date)
    sub_scores = {
        'memory_recall': memory_result['score'],
        'visual_memory': game_result.get('number_score'),
        'pattern_recognition': game_result.get('pair_score'),
        'praxis_camera': game_result.get('camera_score'),
    }
    overall = compute_cognitive_score(sub_scores)
    available_scores = [value for value in sub_scores.values() if value is not None]
    response_consistency_score = round(
        max(0.0, 100.0 - float(np.std(available_scores))), 1
    ) if available_scores else None
    cognitive_result = {
        'assessment_id': assessment_id, 'user_id': get_jwt_identity(),
        'story': assessment.get('assigned_sets', {}).get('story'), 'story_questions': story_questions,
        'story_answers': data.get('story_answers', []), 'story_recall': story_result,
        'game_results': game_result, 'memory_recall': memory_result, 'attention': attention_result,
        'visual_memory': visual_result, 'pattern_recognition': pattern_result, 'orientation': orientation_result,
        'overall_cognitive_score': overall, 'created_at': now,
        'response_consistency_score': response_consistency_score,
        'number_order_result': {
            'completed': game_result.get('number_sequence_completed', False),
            'elapsed_ms': game_result.get('number_elapsed_ms'),
            'completion_time_seconds': game_result.get('number_completion_time_seconds'),
            'errors': game_result.get('number_errors', 0),
            'correct_clicks': game_result.get('number_correct_clicks', 0),
            'incorrect_clicks': game_result.get('number_incorrect_clicks', 0),
            'time_score': game_result.get('number_time_score', 0.0),
            'error_penalty': game_result.get('number_error_penalty', 0.0),
            'final_task_score': game_result.get('number_final_task_score', 0.0),
            'grid_layout': game_result.get('number_grid_layout', []),
            'intervals_ms': game_result.get('number_intervals_ms', []),
            'score': game_result.get('number_score', 0.0),
        },
        'pairup_result': {
            'pairup_completion_time': game_result.get('pairup_completion_time'),
            'pairup_attempts': game_result.get('pairup_attempts', 0),
            'pairup_correct_matches': game_result.get('pairup_correct_matches', 0),
            'pairup_incorrect_attempts': game_result.get('pairup_incorrect_attempts', 0),
            'pairup_accuracy': game_result.get('pairup_accuracy', 0.0),
            'pairup_time_score': game_result.get('pairup_time_score', 0.0),
            'pairup_performance_score': game_result.get('pairup_performance_score', 0.0),
        },
        'camera_capture_result': {
            'prompted_numbers': data.get('game_results', {}).get('camera_session', {}).get('prompted_numbers', []),
            'accepted_captures': data.get('game_results', {}).get('camera_session', {}).get('accepted_captures', []),
            'recalled_numbers': data.get('game_results', {}).get('camera_session', {}).get('recalled_numbers', []),
            'praxis_trials': game_result.get('praxis_trials', []),
            'sequence_score': game_result.get('camera_sequence_score', 0.0),
            'recall_score': game_result.get('camera_recall_score', 0.0),
            'recall_accuracy': game_result.get('camera_recall_accuracy', 0.0),
            'recall_correct': game_result.get('camera_recall_correct', 0),
            'recall_total': game_result.get('camera_recall_total', 0),
        },
    }
    cognitive_result['breakdown'] = cognitive_breakdown(
        {
            'memory_recall': memory_result,
            'story_recall': story_result,
            'attention': attention_result,
            'visual_memory': {'score': game_result.get('number_score')},
            'pattern_recognition': {'score': game_result.get('pair_score')},
            'praxis_camera': {'score': game_result.get('camera_score')},
        },
        game_result,
        cognitive_result['overall_cognitive_score'],
    )
    result = db.cognitive_tests.insert_one(cognitive_result)
    db.assessments.update_one({'_id': ObjectId(assessment_id)}, {'$set': {'cognitive_result': {**cognitive_result, '_id': str(result.inserted_id)}}})
    cognitive_result['_id'] = str(result.inserted_id)
    cognitive_result['created_at'] = cognitive_result['created_at'].isoformat()
    return jsonify(cognitive_result=cognitive_result), 201
