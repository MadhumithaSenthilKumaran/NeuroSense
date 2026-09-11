import random
import re
from datetime import datetime, timedelta

STORY_BANK = [
    {
        "id": "market_story",
        "story": (
            "Ava left home early with her brother and walked to the market near the blue door. "
            "She carried a red bag and bought apples, bread, and a small basket of oranges. "
            "On the way back, she remembered to stop at the bakery and ask for the receipt before leaving."
        ),
        "questions": [
            {"question": "Where did Ava go in the morning?", "answer": "the market"},
            {"question": "What color was the door near the market?", "answer": "blue"},
            {"question": "What did Ava buy first?", "answer": "apples"},
            {"question": "What did she remember to ask for before leaving?", "answer": "the receipt"},
        ],
        "delayed_questions": [
            {"question": "What did Ava carry with her?", "answer": "a red bag"},
            {"question": "Who went with Ava?", "answer": "her brother"},
            {"question": "What did she buy besides apples?", "answer": "bread and oranges"},
            {"question": "Where did she stop on the return trip?", "answer": "the bakery"},
        ],
        "speech_passages": [
            "Ava went to the market near the blue door and bought apples, bread, and oranges. She carried a red bag and made sure to keep her receipt.",
            "On her way home, Ava stopped at the bakery and checked the receipt before leaving the market. She remembered the route and walked back with her brother.",
            "The market was busy, but Ava stayed calm and bought fruit and bread from the vendors by the blue door before heading home.",
        ],
    },
    {
        "id": "garden_story",
        "story": (
            "Daniel spent the afternoon in the garden behind his apartment building. He watered the tomato plants, "
            "moved the chair near the fence, and noticed a yellow bird perched on the wall. Later, he wrote a short note "
            "to his sister about the flowers and the warm weather."
        ),
        "questions": [
            {"question": "Where was Daniel in the afternoon?", "answer": "the garden"},
            {"question": "What color was the bird?", "answer": "yellow"},
            {"question": "What did he do to the tomato plants?", "answer": "watered them"},
            {"question": "Who did he write the note to?", "answer": "his sister"},
        ],
        "delayed_questions": [
            {"question": "What was by the fence?", "answer": "a chair"},
            {"question": "What kind of bird did Daniel notice?", "answer": "a yellow bird"},
            {"question": "Why did he move the chair?", "answer": "to sit near the fence"},
            {"question": "What did he write about?", "answer": "flowers and warm weather"},
        ],
        "speech_passages": [
            "Daniel watered the tomatoes in the garden and noticed a yellow bird on the wall before writing a note to his sister.",
            "The garden behind the apartment was warm and bright. Daniel moved the chair near the fence and checked the flowers before going inside.",
            "After watering the plants, Daniel wrote a short note about the garden and the sunny weather to his sister.",
        ],
    },
    {
        "id": "library_story",
        "story": (
            "Nina visited the library after lunch and borrowed a guide to astronomy. She sat at a table by the window, "
            "wrote down three key facts about the moon, and then returned the book to the front desk before meeting her friend."
        ),
        "questions": [
            {"question": "Where did Nina go after lunch?", "answer": "the library"},
            {"question": "What did she borrow?", "answer": "a guide to astronomy"},
            {"question": "Where did she sit?", "answer": "by the window"},
            {"question": "What did she return before meeting her friend?", "answer": "the book"},
        ],
        "delayed_questions": [
            {"question": "What topic was the book about?", "answer": "astronomy"},
            {"question": "How many facts did Nina write down?", "answer": "three"},
            {"question": "Where was her table?", "answer": "by the window"},
            {"question": "What did she do before meeting her friend?", "answer": "returned the book"},
        ],
        "speech_passages": [
            "Nina went to the library after lunch and borrowed a guide about astronomy before sitting by the window and writing notes.",
            "At the library, Nina took notes on the moon and returned the book to the desk before meeting her friend outside.",
            "The astronomy guide was helpful, and Nina remembered the title, the moon facts, and the route back to the front desk.",
        ],
    },
]

# ---------------------------------------------------------------------------
# Fixed 3-session assessment schedule: Day 1, Day 4, Day 7.
# SESSION_DAY_LABELS is what we show the user ("Day 1" / "Day 4" / "Day 7").
# SESSION_DAY_OFFSETS is how many days after the Day-1 (baseline) date each
# session actually falls on: 0, +3, +6.
# ---------------------------------------------------------------------------
SESSION_DAY_LABELS = {1: 1, 2: 4, 3: 7}
SESSION_DAY_OFFSETS = {1: 0, 2: 3, 3: 6}


def _local_now():
    """Use the machine's local timezone (not naive UTC) so 'today' lines up
    with what the user actually sees on their clock."""
    return datetime.now().astimezone()


def _difficulty_from_stress(stress_level):
    stress = float(stress_level or 0)
    if stress <= 3:
        return "easy"
    if stress <= 7:
        return "moderate"
    return "challenging"


def _session_due_date(baseline_date, session_number):
    """baseline_date is the datetime the user completed Session 1 (Day 1)."""
    if session_number not in SESSION_DAY_OFFSETS:
        raise ValueError("Session number must be 1, 2, or 3")
    offset = SESSION_DAY_OFFSETS[session_number]
    return baseline_date + timedelta(days=offset)


def get_session_lock_status(baseline_date, session_number, now=None):
    """
    Determines whether a session can be taken right now.

    A session is only unlocked on its exact scheduled calendar day
    (e.g. Session 2 can ONLY be taken on Day 4, not before and not after
    without a reschedule). Returns a dict the frontend can render directly.
    """
    now = now or _local_now()
    due = _session_due_date(baseline_date, session_number)

    if now.date() < due.date():
        days_remaining = (due.date() - now.date()).days
        return {
            "unlocked": False,
            "status": "too_early",
            "session_label": f"Day {SESSION_DAY_LABELS[session_number]}",
            "scheduled_date": due.strftime("%Y-%m-%d"),
            "scheduled_display": due.strftime("%B %d, %Y"),
            "days_remaining": days_remaining,
            "message": (
                f"Day {SESSION_DAY_LABELS[session_number]} isn't available yet. "
                f"Come back on {due.strftime('%B %d, %Y')} "
                f"({days_remaining} day{'s' if days_remaining != 1 else ''} from now)."
            ),
        }

    if now.date() > due.date():
        return {
            "unlocked": False,
            "status": "missed",
            "session_label": f"Day {SESSION_DAY_LABELS[session_number]}",
            "scheduled_date": due.strftime("%Y-%m-%d"),
            "scheduled_display": due.strftime("%B %d, %Y"),
            "days_remaining": 0,
            "message": (
                f"Day {SESSION_DAY_LABELS[session_number]} ({due.strftime('%B %d, %Y')}) has passed. "
                "Please contact your care provider to reschedule this session."
            ),
        }

    return {
        "unlocked": True,
        "status": "available",
        "session_label": f"Day {SESSION_DAY_LABELS[session_number]}",
        "scheduled_date": due.strftime("%Y-%m-%d"),
        "scheduled_display": due.strftime("%B %d, %Y"),
        "days_remaining": 0,
        "message": f"Day {SESSION_DAY_LABELS[session_number]} assessment is available today.",
    }


def build_session_plan(session_number, stress_level=0, prior_story=None, baseline_date=None, now=None):
    """
    baseline_date: the datetime Session 1 (Day 1) was completed. Required for
    session_number 2 and 3 so we can enforce the Day 4 / Day 7 lock and keep
    using the SAME story shown on Day 1.
    """
    difficulty = _difficulty_from_stress(stress_level)
    now = now or _local_now()

    if session_number not in (1, 2, 3):
        raise ValueError("Session number must be 1, 2, or 3")

    # --- Sessions 2 and 3: enforce schedule + story continuity -----------
    if session_number in (2, 3):
        if not baseline_date:
            raise ValueError("baseline_date (Day 1 completion date) is required for session 2 and 3")

        lock_status = get_session_lock_status(baseline_date, session_number, now=now)
        if not lock_status["unlocked"]:
            return {
                "session_number": session_number,
                "locked": True,
                **lock_status,
            }

        # The story MUST be the one already shown to the user on Day 1 -
        # never substitute a random story for the delayed-recall sessions,
        # or the recall questions won't correspond to anything the user saw.
        if not prior_story or not prior_story.get("story_id"):
            raise ValueError(
                "prior_story with a 'story_id' from Session 1 is required to build "
                "story-based questions for session 2/3"
            )
        story_entry = next((item for item in STORY_BANK if item["id"] == prior_story["story_id"]), None)
        if not story_entry:
            # Fallback for a custom/imported story: reuse its own questions
            # instead of pulling in an unrelated story from the bank.
            story_entry = {
                "id": prior_story["story_id"],
                "story": prior_story.get("story", ""),
                "questions": prior_story.get("questions", []),
                "delayed_questions": prior_story.get("delayed_questions", prior_story.get("questions", [])),
                "speech_passages": prior_story.get("speech_passages", []),
            }

        delayed_questions = story_entry.get("delayed_questions") or story_entry.get("questions", [])
        if difficulty == "challenging":
            delayed_questions = delayed_questions[:]

        next_session_date = None
        if session_number == 2:
            next_due = _session_due_date(baseline_date, 3)
            next_session_date = next_due.strftime("%Y-%m-%d")

        return {
            "session_number": session_number,
            "session_label": f"Day {SESSION_DAY_LABELS[session_number]}",
            "locked": False,
            "difficulty": difficulty,
            "story_id": story_entry["id"],
            # Story text is intentionally NOT re-shown here - Session 2/3
            # test delayed recall of the Day 1 story, so only the
            # story-based questions are returned.
            "questions": delayed_questions,
            "speech_passage": random.choice(
                story_entry.get("speech_passages") or ["A short reading passage for delayed memory assessment."]
            ),
            "next_session_date": next_session_date,
            "request_video_next_session": False,
        }

    # --- Session 1: pick (or accept) a story and set the baseline date ---
    story_entry = None
    if prior_story and isinstance(prior_story, dict):
        if prior_story.get("story_id"):
            story_entry = next((item for item in STORY_BANK if item["id"] == prior_story["story_id"]), None)
        if not story_entry and prior_story.get("story"):
            story_entry = {
                "id": "custom_story",
                "story": prior_story["story"],
                "questions": prior_story.get("questions", []),
                "delayed_questions": prior_story.get("delayed_questions", []),
                "speech_passages": prior_story.get("speech_passages", []),
            }
    if not story_entry:
        story_entry = random.choice(STORY_BANK)

    question_pool = story_entry["questions"]
    if difficulty == "challenging":
        question_pool = question_pool[:]

    baseline_for_schedule = now
    next_due = _session_due_date(baseline_for_schedule, 2)

    return {
        "session_number": 1,
        "session_label": f"Day {SESSION_DAY_LABELS[1]}",
        "locked": False,
        "difficulty": difficulty,
        "story_id": story_entry["id"],
        "story": story_entry["story"],
        "questions": question_pool,
        # The frontend/DB must persist this baseline_date and pass it back
        # into build_session_plan() for session_number=2 and 3.
        "baseline_date": baseline_for_schedule.strftime("%Y-%m-%d"),
        "next_session_date": next_due.strftime("%Y-%m-%d"),
        "next_session_label": f"Day {SESSION_DAY_LABELS[2]}",
        "request_video_next_session": False,
    }


def _normalize_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _calc_word_overlap(transcript, passage):
    if not transcript or not passage:
        return 0.0
    passage_words = set(_normalize_text(passage).split())
    transcript_words = set(_normalize_text(transcript).split())
    if not passage_words:
        return 0.0
    overlap = len(passage_words & transcript_words)
    return round((overlap / len(passage_words)) * 100, 1)


def _coerce_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _answer_matches(user_answer, correct_answer):
    """True if the user's answer is an exact or close-enough match to the
    expected answer (handles short phrase answers like 'the market')."""
    ua = _normalize_text(user_answer)
    ca = _normalize_text(correct_answer)
    if not ua or not ca:
        return False
    if ua == ca or ca in ua or ua in ca:
        return True
    ca_words = set(ca.split())
    ua_words = set(ua.split())
    if not ca_words:
        return False
    overlap = len(ca_words & ua_words) / len(ca_words)
    return overlap >= 0.6


def score_memory_test(questions, user_answers):
    """
    Grades the story-recall questions the user actually answered this
    session and turns them into a memory_score out of 100. This is the
    piece that was missing before, which is why the final report showed
    'Cognitive score: 0/100' - nothing was ever scoring the user's answers.

    questions: list of {"question": ..., "answer": ...} (from build_session_plan)
    user_answers: either
        - a dict keyed by question index (as str or int) or by question text, or
        - a list of answers in the same order as `questions`
    """
    if not questions:
        return {"memory_score": 0.0, "correct_count": 0, "total": 0, "details": []}

    details = []
    correct_count = 0
    for idx, q in enumerate(questions):
        if isinstance(user_answers, dict):
            given = (
                user_answers.get(str(idx))
                or user_answers.get(idx)
                or user_answers.get(q["question"])
            )
        elif isinstance(user_answers, (list, tuple)):
            given = user_answers[idx] if idx < len(user_answers) else None
        else:
            given = None

        is_correct = _answer_matches(given, q["answer"])
        if is_correct:
            correct_count += 1
        details.append({
            "question": q["question"],
            "expected_answer": q["answer"],
            "given_answer": given,
            "correct": is_correct,
        })

    memory_score = round((correct_count / len(questions)) * 100, 2)
    return {
        "memory_score": memory_score,
        "correct_count": correct_count,
        "total": len(questions),
        "details": details,
    }


def analyze_speech_response(passage, transcript=None, duration_s=0, speech_rate_wpm=None,
                            pause_duration_s=0, total_words=0, behavioral_notes=None):
    expected_rate = 150.0
    rate = _coerce_float(speech_rate_wpm, expected_rate)
    speech_rate_score = max(0, min(100, 100 - abs(rate - expected_rate) * 0.8))

    pause_threshold = max(1.5, (duration_s or 0) * 0.12)
    pause_penalty = max(0.0, _coerce_float(pause_duration_s, 0.0) - pause_threshold)
    pause_rate_score = max(0, min(100, 100 - (pause_penalty * 30)))

    filler_matches = re.findall(r"\b(um|uh|er|like|you know)\b", (transcript or "").lower())
    hesitation = len(filler_matches)
    hesitation_score = max(0, 100 - hesitation * 12)

    completeness = 100.0
    if total_words:
        transcript_words = len((transcript or "").split())
        completeness = max(0.0, min(100.0, (transcript_words / max(1, total_words)) * 100.0))
    incompleteness_score = 100.0 - max(0.0, 100.0 - completeness)

    overlap_score = _calc_word_overlap(transcript, passage)
    mismatch_penalty = max(0.0, 100.0 - overlap_score)
    response_mismatch = round(mismatch_penalty, 2)

    misactions = 0
    if behavioral_notes:
        misactions = len([item for item in behavioral_notes if str(item).lower() in {"misaction", "incomplete", "confused", "off-topic"}])
    misaction_penalty = misactions * 15

    behavioral_score = (
        (speech_rate_score * 0.25)
        + (pause_rate_score * 0.25)
        + (hesitation_score * 0.2)
        + (incompleteness_score * 0.2)
        + ((100.0 - response_mismatch) * 0.1)
        - misaction_penalty
    )
    behavioral_score = max(0.0, min(100.0, round(behavioral_score, 2)))

    requires_video_next_session = behavioral_score < 65 or response_mismatch > 25 or misactions > 0

    return {
        "speech_rate_score": round(speech_rate_score, 2),
        "pause_rate_score": round(pause_rate_score, 2),
        "hesitation_score": round(hesitation_score, 2),
        "incompleteness_score": round(incompleteness_score, 2),
        "behavioral_score": behavioral_score,
        "response_mismatch": round(response_mismatch, 2),
        "hesitation": hesitation,
        "misactions": misactions,
        "requires_video_next_session": requires_video_next_session,
        "word_overlap_score": overlap_score,
    }


def _score_to_band(score):
    if score >= 80:
        return "strong"
    if score >= 65:
        return "steady"
    if score >= 45:
        return "watch"
    return "needs_support"


def _rag_task_recommendations(memory_score, speech_score, behavioral_score, stress_level):
    tasks = []
    if memory_score < 70:
        tasks.append("Use daily recall ladders with three-item memory drills and delayed repetition after 10 minutes.")
    if speech_score < 70:
        tasks.append("Practice short reading passages with paced breathing and repeat the same sentence at a slower, measured pace.")
    if behavioral_score < 70:
        tasks.append("Add structured attention tasks and a brief social conversation check-in to monitor focus and response consistency.")
    if stress_level >= 7:
        tasks.append("Add a 5-minute mindfulness or breathing routine before cognitive work to lower stress-related interference.")
    if not tasks:
        tasks.append("Maintain the current routine and introduce a light delayed-recall challenge once per week.")
    return tasks


def generate_cognitive_final_report(session_memory_results=None, speech_scores=None, behavioral_scores=None,
                                   performance_trend=None, recommendations=None, memory_scores=None):
    """
    session_memory_results: list of results from score_memory_test() for each
    session (1, 2, 3) - i.e. the ACTUAL points the user earned on the
    story-recall questions they answered. This replaces the old
    `memory_scores` list of pre-computed numbers, which is what let the
    cognitive score silently come out as 0 when nothing upstream ever
    graded the user's answers.
    """
    if session_memory_results is None:
        session_memory_results = [
            {"memory_score": score, "correct_count": 0, "total": 0}
            for score in (memory_scores or [])
        ]
    memory_scores = [r["memory_score"] for r in session_memory_results if r]
    avg_memory = round(sum(memory_scores) / max(1, len(memory_scores)), 2) if memory_scores else 0.0
    avg_speech = round(sum(speech_scores) / max(1, len(speech_scores)), 2) if speech_scores else 0.0
    avg_behavior = round(sum(behavioral_scores) / max(1, len(behavioral_scores)), 2) if behavioral_scores else 0.0

    total_correct = sum(r.get("correct_count", 0) for r in session_memory_results if r)
    total_questions = sum(r.get("total", 0) for r in session_memory_results if r)

    trend = performance_trend or {}
    report = {
        "overall_memory_score": avg_memory,
        "overall_speech_score": avg_speech,
        "overall_behavioral_score": avg_behavior,
        "memory_band": _score_to_band(avg_memory),
        "speech_band": _score_to_band(avg_speech),
        "behavioral_band": _score_to_band(avg_behavior),
        "session_memory_breakdown": session_memory_results,
        "total_recall_correct": total_correct,
        "total_recall_questions": total_questions,
        "performance_trend": trend,
        "recommendations": list(recommendations or []),
        "summary": (
            "This multi-session review compares recall, speech fluency, and behavioral consistency across sessions "
            "to highlight meaningful changes over time."
        ),
    }

    if not report["recommendations"]:
        report["recommendations"] = _rag_task_recommendations(avg_memory, avg_speech, avg_behavior, 0)

    return report


def generate_session_recommendations(memory_score, speech_score, behavioral_score, stress_level):
    tasks = _rag_task_recommendations(memory_score, speech_score, behavioral_score, stress_level)
    summary = {
        "memory_task": tasks[0] if tasks else "Practice short recall drills.",
        "speech_task": tasks[1] if len(tasks) > 1 else "Read one paragraph aloud using slower, deliberate pacing.",
        "behavioral_task": tasks[2] if len(tasks) > 2 else "Track attention with a simple response consistency check.",
    }
    if stress_level >= 7:
        next_assessment_suggestion = "Schedule the next assessment within 4-6 weeks and prioritize stress management before the next review."
    elif memory_score < 70:
        next_assessment_suggestion = "Plan the next assessment in 3 months to track memory changes and confirm whether the routine is helping."
    else:
        next_assessment_suggestion = "Plan the next assessment in 6 months to monitor trends and keep early changes visible."

    llm_prompt = (
        "Create a personalized cognitive care plan for a patient with stress level "
        f"{stress_level}, memory score {memory_score}, speech score {speech_score}, and behavioral score {behavioral_score}. "
        "Use evidence-based memory, speech pacing, and stress-reduction tasks; note any video review requirement."
    )
    return {
        "tasks": tasks,
        "summary": summary,
        "llm_prompt": llm_prompt,
        "uses_rag": True,
        "next_assessment_suggestion": next_assessment_suggestion,
    }