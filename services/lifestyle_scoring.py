"""
Wrapper exposing lifestyle_scoring functions under services.lifestyle_scoring
by delegating to the top-level lifestyle_scoring.py module.
"""
try:
    from lifestyle_scoring import *  # noqa: F401,F403
except Exception:
    LIFESTYLE_QUESTIONS = []
    CONCERN_QUESTIONS = []
    CONCERN_SCALE = []

    def score_lifestyle(answers):
        return {"lifestyle_score": None, "elevated_risk_factors": []}

    def score_concern(answers):
        return {"concern_score": None}
