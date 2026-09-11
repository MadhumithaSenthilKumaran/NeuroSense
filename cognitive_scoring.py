"""
Scoring for the Cognitive Assessment module. Each test is scored 0-100
so scores can be combined into a single normalized cognitive_score.
"""

MEMORY_WORDS = ["apple", "river", "chair", "book", "tiger", "window"]
ATTENTION_SEQUENCE = ["A", "3", "B", "7", "C", "9", "D", "2"]
VISUAL_MEMORY_GRID_SIZE = 9


def score_memory_recall(recalled_words: list, memory_words=None) -> dict:
    memory_words = memory_words or MEMORY_WORDS
    recalled_norm = {w.strip().lower() for w in recalled_words if w.strip()}
    correct = recalled_norm & {word.lower() for word in memory_words}
    score = round(100 * len(correct) / len(memory_words), 1)
    return {"score": score, "correct_words": sorted(correct), "total_words": len(memory_words)}


def score_story_recall(answers: list, questions: list) -> dict:
    if not questions:
        return {"score": None, "correct": 0, "total": 0}
    correct = 0
    results = []
    for index, question in enumerate(questions):
        response = str((answers or [])[index] if index < len(answers or []) else "").strip().lower()
        expected = str(question.get("answer", "")).strip().lower()
        matched = bool(response and expected and (expected in response or response in expected))
        correct += int(matched)
        results.append({"question": question.get("question"), "correct": matched})
    return {"score": round(100 * correct / len(questions), 1), "correct": correct, "total": len(questions), "results": results}


def score_reaction_time(reaction_times_ms: list) -> dict:
    """Lower is better. Map typical 200-800ms range onto a 0-100 score."""
    valid = [t for t in reaction_times_ms if isinstance(t, (int, float)) and t > 0]
    if not valid:
        return {"score": None, "avg_ms": None}
    avg_ms = sum(valid) / len(valid)
    # 200ms -> 100, 800ms+ -> 0 (clamped), linear in between.
    score = max(0.0, min(100.0, 100 - ((avg_ms - 200) / (800 - 200)) * 100))
    return {"score": round(score, 1), "avg_ms": round(avg_ms, 1)}


def score_attention(user_answer: str) -> dict:
    # Sequence: A 3 B 7 C 9 D 2  -> "what number came after B?" => 7
    correct_answer = "7"
    correct = str(user_answer).strip() == correct_answer
    return {"score": 100.0 if correct else 0.0, "correct": correct, "expected": correct_answer}


def score_visual_memory(selected_positions: list, target_positions: list) -> dict:
    selected = set(selected_positions or [])
    target = set(target_positions or [])
    if not target:
        return {"score": None}
    correct = selected & target
    score = round(100 * len(correct) / len(target), 1)
    return {"score": score, "correct": len(correct), "total": len(target)}


def score_pattern_recognition(answers: list) -> dict:
    """answers: list of {"question_id", "selected", "correct"} bools already
    resolved client-side against the served pattern set, or resolved here if
    raw indices are passed."""
    if not answers:
        return {"score": None}
    correct_count = sum(1 for a in answers if a.get("selected") == a.get("correct"))
    score = round(100 * correct_count / len(answers), 1)
    return {"score": score, "correct": correct_count, "total": len(answers)}


def score_orientation(answers: dict, current_date: dict) -> dict:
    """
    answers: {year, month, day, city}
    current_date: {year, month, day} (server-side ground truth; city is
    self-reported so it only checks non-empty, not correctness).
    """
    checks = {
        "year": str(answers.get("year", "")).strip() == str(current_date.get("year", "")),
        "month": str(answers.get("month", "")).strip().lower() == str(current_date.get("month", "")).lower(),
        "day": str(answers.get("day", "")).strip() == str(current_date.get("day", "")),
        "city": bool(str(answers.get("city", "")).strip()),
    }
    correct_count = sum(checks.values())
    score = round(100 * correct_count / len(checks), 1)
    return {"score": score, "checks": checks}


def compute_cognitive_score(sub_scores: dict) -> float:
    """
    Weighted composite. Memory and orientation weighted slightly higher as
    they are the most established early markers in cognitive screening
    literature (e.g. MMSE / MoCA domain weighting), reaction time weighted
    lowest since it is the noisiest signal.
    """
    weights = {
        "memory_recall": 0.25,
        "story_recall": 0.15,
        "reaction_time": 0.10,
        "attention": 0.15,
        "visual_memory": 0.15,
        "pattern_recognition": 0.15,
        "orientation": 0.20,
    }
    total_weight = 0.0
    weighted_sum = 0.0
    for key, weight in weights.items():
        val = sub_scores.get(key)
        if val is None:
            continue
        weighted_sum += val * weight
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return round(weighted_sum / total_weight, 1)


def score_game_results(results: dict) -> dict:
    pair = results.get("pair_game", {})
    number = results.get("number_game", {})
    camera = results.get("camera_session", {})
    pair_score = min(100.0, float(pair.get("matched_pairs", 0)) / 8 * 100)
    number_score = 100.0 if number.get("completed") else 0.0
    expected = {str(word).lower() for word in camera.get("expected_words", [])}
    recalled = {str(word).lower() for word in camera.get("recalled_words", [])}
    word_score = 100.0 * len(expected & recalled) / len(expected) if expected else 0.0
    action_duration_ms = camera.get("action_duration_ms")
    action_captured = isinstance(action_duration_ms, (int, float)) and action_duration_ms > 0
    action_score = 100.0 if action_captured else 0.0
    capture_verified = bool(camera.get("capture_verified"))
    camera_score = round((word_score + action_score) / 2, 1)
    return {"score": round((pair_score + number_score + camera_score) / 3, 1), "pair_score": pair_score, "number_score": number_score, "camera_score": camera_score, "camera_words_recalled": len(expected & recalled), "camera_number_expected": camera.get("expected_number"), "camera_number_verification": "captured_for_review" if capture_verified else "not_captured", "action_duration_ms": action_duration_ms, "action_captured": action_captured}