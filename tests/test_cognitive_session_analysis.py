from services.cognitive_session_analysis import (
    build_session_plan,
    analyze_speech_response,
    generate_cognitive_final_report,
)
from cognitive_scoring import score_game_results, score_story_recall
from services.session_assessment import STORY_BANK, SPEECH_BANK, assign_sets, build_cycle_schedule, resolve_story_for_session


def test_session_one_includes_story_and_questions():
    plan = build_session_plan(1, stress_level=4, prior_story=None)
    assert plan["session_number"] == 1
    assert "story" in plan
    assert len(plan["questions"]) >= 2
    assert plan["difficulty"] in {"easy", "moderate", "challenging"}


def test_story_bank_has_fifty_items_and_reuses_across_sessions():
    assert len(STORY_BANK) == 50

    first_story = {"id": "story_01", "story": "Ava went to the market.", "questions": [{"question": "Where did Ava go?", "answer": "the market"}]}
    second_story = resolve_story_for_session(2, prior_story=first_story)
    third_story = resolve_story_for_session(3, prior_story=second_story)

    assert second_story["id"] == first_story["id"]
    assert third_story["id"] == second_story["id"]
    assert second_story["questions"] == first_story["questions"]
    assert third_story["questions"] == second_story["questions"]


def test_cycle_schedule_covers_days_one_three_five_with_same_day_reminders():
    from datetime import datetime, timezone

    schedule = build_cycle_schedule(datetime(2026, 9, 1, tzinfo=timezone.utc))
    assert [item["scheduled_for"] for item in schedule] == ["2026-09-01", "2026-09-03", "2026-09-05"]
    assert [item["reminder_for"] for item in schedule] == ["2026-09-01", "2026-09-03", "2026-09-05"]


def test_speech_bank_has_twenty_distinct_passages_and_assigns_one_without_selector():
    assert len(SPEECH_BANK) == 20
    assignment = assign_sets(used_speech_ids=["speech_01"])
    assert len(assignment["speech"]["options"]) == 1
    assert assignment["speech"]["id"] != "speech_01"


def test_story_answers_are_scored_server_side():
    questions = [{"question": "Where?", "answer": "the market"}, {"question": "What color?", "answer": "blue"}]
    result = score_story_recall(["market", "green"], questions)
    assert result["score"] == 50.0
    assert result["correct"] == 1


def test_pairup_performance_score_uses_accuracy_and_prototype_time_band():
    result = score_game_results({
        "pair_game": {
            "completion_time_seconds": 25,
            "attempts": 10,
            "correct_matches": 8,
            "incorrect_attempts": 2,
        },
        "number_game": {},
        "camera_session": {},
    })
    assert result["pairup_time_score"] == 90.0
    assert result["pairup_accuracy"] == 80.0
    assert result["pairup_performance_score"] == 84.0
    assert result["pair_score"] == 84.0


def test_number_order_score_applies_time_band_and_error_penalty():
    result = score_game_results({
        "pair_game": {},
        "number_game": {
            "completed": True,
            "completion_time_seconds": 34,
            "errors": 2,
            "grid_layout": list(range(1, 26)),
        },
        "camera_session": {},
    })
    assert result["number_time_score"] == 7.0
    assert result["number_error_penalty"] == 1.0
    assert result["number_task_score"] == 6.0
    assert result["number_score"] == 60.0


def test_pairup_accuracy_and_incomplete_number_task_are_zero_safely():
    result = score_game_results({
        "pair_game": {"attempts": 0, "correct_matches": 0},
        "number_game": {"completed": False, "errors": 3},
        "camera_session": {},
    })
    assert result["pairup_accuracy"] == 0.0
    assert result["pairup_performance_score"] == 0.0
    assert result["number_task_score"] == 0.0


def test_speech_analysis_returns_behavior_metrics():
    passage = "Ava went to the market and bought apples before returning home."
    result = analyze_speech_response(
        passage,
        transcript="Ava went to the market and bought apples before returning home.",
        duration_s=14.0,
        speech_rate_wpm=120,
        pause_duration_s=1.8,
        total_words=len(passage.split()),
    )
    assert "speech_rate_score" in result
    assert "pause_rate_score" in result
    assert "behavioral_score" in result
    assert result["response_mismatch"] >= 0


def test_final_report_includes_recommendations_and_scores():
    report = generate_cognitive_final_report(
        memory_scores=[88, 75, 80],
        speech_scores=[90, 82, 85],
        behavioral_scores=[70, 60, 65],
        performance_trend={"memory": [88, 75, 80], "speech": [90, 82, 85]},
        recommendations=["Practice recall drills", "Use short attention exercises"],
    )
    assert report["overall_memory_score"] >= 0
    assert report["overall_speech_score"] >= 0
    assert report["overall_behavioral_score"] >= 0
    assert len(report["recommendations"]) >= 1
