"""
Scoring for the Cognitive Assessment module. Each test is scored 0-100
so scores can be combined into a single normalized cognitive_score.
"""

MEMORY_WORDS = ["apple", "river", "chair", "book", "tiger", "window"]
ATTENTION_SEQUENCE = ["A", "3", "B", "7", "C", "9", "D", "2"]
VISUAL_MEMORY_GRID_SIZE = 9

COGNITIVE_WEIGHTS = {
    "memory_recall": 0.25,
    "visual_memory": 0.25,
    "pattern_recognition": 0.25,
    "praxis_camera": 0.25,
}

COGNITIVE_EXPLANATIONS = {
    "memory_recall": "Measures immediate recall of the displayed words.",
    "visual_memory": "Measures the number-order task: selecting numbers in the requested sequence.",
    "pattern_recognition": "Measures the pair-up game: matching the cards accurately.",
    "praxis_camera": "Measures finger-number accuracy and movement quality from the camera recording.",
}

COGNITIVE_NAMES = {
    "memory_recall": "Memory Recall",
    "visual_memory": "Number Order",
    "pattern_recognition": "Pair-Up Visual Memory",
    "praxis_camera": "Camera Finger Praxis",
}


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
    weights = COGNITIVE_WEIGHTS
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


def cognitive_breakdown(sub_results: dict, game_result: dict, overall_score: float) -> dict:
    """Return an auditable explanation of every cognitive score contribution."""
    sub_scores = {key: (value or {}).get("score") for key, value in sub_results.items()}
    available_weight = sum(
        COGNITIVE_WEIGHTS[key]
        for key, value in sub_scores.items()
        if key in COGNITIVE_WEIGHTS and value is not None
    )
    parts = []
    for key, weight in COGNITIVE_WEIGHTS.items():
        score = sub_scores.get(key)
        normalized_weight = weight / available_weight if score is not None and available_weight else 0.0
        parts.append({
            "key": key,
            "name": COGNITIVE_NAMES[key],
            "score": score,
            "weight_percent": round(normalized_weight * 100, 1),
            "contribution_points": round((score or 0) * normalized_weight, 1) if score is not None else None,
            "explanation": COGNITIVE_EXPLANATIONS[key],
            "game_breakdown": game_result if key == "praxis_camera" else None,
        })
    return {
        "overall_score": overall_score,
        "method": "Only the four evaluated components are included: memory recall, number order, pair matching, and camera finger praxis. Each contributes 25%.",
        "parts": parts,
    }


def score_game_results(results: dict) -> dict:
    pair = results.get("pair_game", {})
    number = results.get("number_game", {})
    camera = results.get("camera_session", {})
    pair_attempts = max(0, int(pair.get("attempts", 0) or 0))
    pair_correct = max(0, min(8, int(pair.get("correct_matches", pair.get("matched_pairs", 0)) or 0)))
    pair_incorrect = max(0, int(pair.get("incorrect_attempts", max(0, pair_attempts - pair_correct)) or 0))
    pair_completion_ms = pair.get("completion_time_ms")
    pair_completion_seconds = pair.get("completion_time_seconds")
    if pair_completion_seconds is None and isinstance(pair_completion_ms, (int, float)):
        pair_completion_seconds = pair_completion_ms / 1000
    pair_accuracy = round(100 * pair_correct / pair_attempts, 1) if pair_attempts else 0.0
    # Prototype research bands, not clinical norms or diagnostic thresholds.
    if pair_completion_seconds is None:
        pair_time_score = 0.0
    elif pair_completion_seconds <= 20:
        pair_time_score = 100.0
    elif pair_completion_seconds <= 30:
        pair_time_score = 90.0
    elif pair_completion_seconds <= 40:
        pair_time_score = 75.0
    elif pair_completion_seconds <= 60:
        pair_time_score = 55.0
    else:
        pair_time_score = 35.0
    pair_performance_score = round(0.60 * pair_accuracy + 0.40 * pair_time_score, 1)
    pair_score = pair_performance_score

    elapsed_ms = number.get("completion_time_ms", number.get("elapsed_ms"))
    completed = bool(number.get("completed"))
    completion_seconds = number.get("completion_time_seconds")
    if completion_seconds is None and isinstance(elapsed_ms, (int, float)):
        completion_seconds = elapsed_ms / 1000
    # Prototype research bands, not clinical norms or diagnostic thresholds.
    if not completed or completion_seconds is None:
        number_time_score = 0.0
    elif completion_seconds <= 20:
        number_time_score = 10.0
    elif completion_seconds <= 25:
        number_time_score = 9.0
    elif completion_seconds <= 30:
        number_time_score = 8.0
    elif completion_seconds <= 35:
        number_time_score = 7.0
    elif completion_seconds <= 40:
        number_time_score = 6.0
    elif completion_seconds <= 50:
        number_time_score = 5.0
    elif completion_seconds <= 60:
        number_time_score = 4.0
    elif completion_seconds <= 75:
        number_time_score = 3.0
    elif completion_seconds <= 90:
        number_time_score = 2.0
    else:
        number_time_score = 1.0
    number_errors = max(0, int(number.get("errors", number.get("incorrect_clicks", 0)) or 0))
    number_error_penalty = number_errors * 0.5
    number_task_score = round(max(0.0, min(10.0, number_time_score - number_error_penalty)), 1)
    number_score = round(number_task_score * 10, 1)
    praxis_trials = camera.get("praxis_trials", [])
    praxis_score = (sum(bool(trial.get("is_correct_match")) for trial in praxis_trials) / len(praxis_trials) * 100) if praxis_trials else 0.0
    prompted_sequence = [int(number) for number in camera.get("prompted_numbers", []) if str(number).isdigit()]
    recalled_sequence = [int(number) for number in camera.get("recalled_numbers", []) if str(number).isdigit()]
    camera_recall_total = len(prompted_sequence)
    camera_recall_correct = sum(
        expected == recalled_sequence[index]
        for index, expected in enumerate(prompted_sequence)
        if index < len(recalled_sequence)
    )
    camera_recall_score = round(100 * camera_recall_correct / camera_recall_total, 1) if camera_recall_total else 0.0
    expected = {str(word).lower() for word in camera.get("expected_words", [])}
    recalled = {str(word).lower() for word in camera.get("recalled_words", [])}
    word_score = 100.0 * len(expected & recalled) / len(expected) if expected else 0.0
    action_duration_ms = camera.get("action_duration_ms")
    action_captured = isinstance(action_duration_ms, (int, float)) and action_duration_ms > 0
    action_score = 100.0 if action_captured else 0.0
    capture_verified = bool(camera.get("capture_verified"))
    correct_trials = sum(bool(trial.get("is_correct_match")) for trial in praxis_trials)
    camera_sequence_score = round(100 * correct_trials / len(praxis_trials), 1) if praxis_trials else 0.0
    camera_score = camera_sequence_score if praxis_trials else 0.0
    return {
        "score": round((pair_score + number_score + camera_score) / 3, 1),
        "pair_score": pair_score,
        "pairup_completion_time": pair_completion_seconds,
        "pairup_attempts": pair_attempts,
        "pairup_correct_matches": pair_correct,
        "pairup_incorrect_attempts": pair_incorrect,
        "pairup_accuracy": pair_accuracy,
        "pairup_time_score": pair_time_score,
        "pairup_performance_score": pair_performance_score,
        "number_score": number_score,
        "number_task_score": number_task_score,
        "number_elapsed_ms": elapsed_ms,
        "number_completion_time_seconds": completion_seconds,
        "number_sequence_completed": completed,
        "number_errors": number_errors,
        "number_correct_clicks": number.get("correct_clicks", 25 if completed else 0),
        "number_incorrect_clicks": number.get("incorrect_clicks", number_errors),
        "number_time_score": number_time_score,
        "number_error_penalty": number_error_penalty,
        "number_final_task_score": number_task_score,
        "number_grid_layout": number.get("grid_layout", []),
        "number_intervals_ms": number.get("intervals_ms", []),
        "camera_score": camera_score,
        "camera_recall_score": camera_recall_score,
        "camera_recall_correct": camera_recall_correct,
        "camera_recall_total": camera_recall_total,
        "camera_recalled_numbers": recalled_sequence,
        "camera_recall_accuracy": camera_recall_score,
        "camera_sequence_score": camera_sequence_score,
        "camera_correct_trials": correct_trials,
        "camera_total_trials": len(praxis_trials),
        "camera_words_recalled": len(expected & recalled),
        "camera_number_expected": camera.get("expected_number"),
        "camera_number_verification": "captured_for_review" if capture_verified else "not_captured",
        "praxis_trials": praxis_trials,
        "accepted_captures": camera.get("accepted_captures", []),
        "action_duration_ms": action_duration_ms,
        "action_captured": action_captured,
    }