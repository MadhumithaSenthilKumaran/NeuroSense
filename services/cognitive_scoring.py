"""
Wrapper exposing cognitive_scoring functions under services.cognitive_scoring
by delegating to the top-level cognitive_scoring.py module.
"""
try:
    from cognitive_scoring import *  # noqa: F401,F403
except Exception:
    # If import fails, define safe fallbacks to avoid ImportError during app startup.
    MEMORY_WORDS = []
    ATTENTION_SEQUENCE = []

    def score_memory_recall(recalled_words):
        return {"score": None, "correct_words": [], "total_words": 0}

    def score_reaction_time(reaction_times_ms):
        return {"score": None, "avg_ms": None}

    def score_attention(user_answer):
        return {"score": None, "correct": False, "expected": None}

    def score_visual_memory(selected_positions, target_positions):
        return {"score": None}

    def score_pattern_recognition(answers):
        return {"score": None, "correct": 0, "total": 0}

    def score_orientation(answers, current_date):
        return {"score": None, "checks": {}}

    def compute_cognitive_score(sub_scores):
        return 0.0

    def score_game_results(results):
        return {"score": 0.0, "pair_score": 0.0, "number_score": 0.0, "camera_score": 0.0}
