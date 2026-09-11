from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from extensions import get_db
from services.cognitive_scoring import (
    MEMORY_WORDS, ATTENTION_SEQUENCE, score_memory_recall, score_attention,
    score_visual_memory, score_pattern_recognition, score_orientation,
    score_story_recall, score_game_results, compute_cognitive_score,
)

cognitive_bp = Blueprint('cognitive', __name__)

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
    sub_scores = {'memory_recall': memory_result['score'], 'story_recall': story_result['score'], 'attention': attention_result['score'], 'visual_memory': visual_result['score'], 'pattern_recognition': pattern_result['score'], 'orientation': orientation_result['score']}
    overall = compute_cognitive_score(sub_scores)
    cognitive_result = {
        'assessment_id': assessment_id, 'user_id': get_jwt_identity(),
        'story': assessment.get('assigned_sets', {}).get('story'), 'story_questions': story_questions,
        'story_answers': data.get('story_answers', []), 'story_recall': story_result,
        'game_results': game_result, 'memory_recall': memory_result, 'attention': attention_result,
        'visual_memory': visual_result, 'pattern_recognition': pattern_result, 'orientation': orientation_result,
        'overall_cognitive_score': round((overall + game_result['score']) / 2, 1), 'created_at': now,
    }
    result = db.cognitive_tests.insert_one(cognitive_result)
    db.assessments.update_one({'_id': ObjectId(assessment_id)}, {'$set': {'cognitive_result': {**cognitive_result, '_id': str(result.inserted_id)}}})
    cognitive_result['_id'] = str(result.inserted_id)
    cognitive_result['created_at'] = cognitive_result['created_at'].isoformat()
    return jsonify(cognitive_result=cognitive_result), 201
