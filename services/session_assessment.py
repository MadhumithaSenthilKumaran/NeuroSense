import csv
import random
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


SESSION_OFFSETS = {1: 0, 2: 2, 3: 4}
TESTS = ["lifestyle", "cognitive", "speech", "self_concern"]


def _story_bank():
    bank = []
    places = ["library", "market", "garden", "station", "museum"]
    names = ["Ava", "Daniel", "Nina", "Omar", "Mia", "Leo", "Sara", "Iris", "Noah", "Lina"]
    for index in range(50):
        place = places[index % len(places)]
        name = names[index % len(names)]
        color = ["blue", "yellow", "green", "red", "orange"][index % 5]
        item = ["apples", "a notebook", "flowers", "tickets", "a camera"][index % 5]
        bank.append({
            "id": f"story_{index + 1:02d}",
            "story": f"{name} visited the {place} after lunch. A {color} sign stood near the entrance, and {name} carried {item}. Before going home, {name} wrote down two details at table {index + 1} and thanked a helpful neighbor.",
            "questions": [
                {"question": f"Where did {name} go?", "answer": f"the {place}"},
                {"question": "What color was the sign?", "answer": color},
                {"question": f"What did {name} carry?", "answer": item},
                {"question": "How many details were written down?", "answer": "two"},
            ],
        })
    return bank


def _memory_bank():
    themes = ["amber", "cedar", "coral", "dawn", "elm", "frost", "harbor", "indigo", "juniper", "linen"]
    return [{"id": f"memory_{index + 1:02d}", "words": [
        themes[index % 10], f"{themes[(index + 1) % 10]}-{index + 1}",
        f"lantern-{index + 1}", f"meadow-{index + 1}", f"pencil-{index + 1}", f"ticket-{index + 1}",
    ]} for index in range(50)]


def _speech_bank():
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "Labeled_speech_data.csv"
    passages = []
    with dataset_path.open(newline="", encoding="utf-8-sig") as dataset:
        for row in csv.DictReader(dataset):
            paragraph = re.sub(r"\s+", " ", (row.get("Passage_Content", "") or "").strip())
            if paragraph and paragraph not in [item["paragraph"] for item in passages]:
                passages.append({
                    "id": row.get("Passage_ID") or f"speech_{len(passages) + 1:03d}",
                    "title": row.get("Passage_Title") or f"Passage {len(passages) + 1}",
                    "paragraph": paragraph,
                })
    return passages


STORY_BANK = _story_bank()
MEMORY_BANK = _memory_bank()
SPEECH_BANK = _speech_bank()


def _unused(bank, used_ids):
    available = [item for item in bank if item["id"] not in used_ids]
    if not available:
        raise ValueError("The assignment bank is exhausted for this user")
    return random.choice(available)


def resolve_story_for_session(session_number, prior_story=None):
    if session_number == 1:
        return _unused(STORY_BANK, set())

    if prior_story and isinstance(prior_story, dict):
        if prior_story.get("story") or prior_story.get("questions"):
            return {
                "id": prior_story.get("id") or prior_story.get("story_id") or "memory_story",
                "story": prior_story.get("story") or "",
                "questions": prior_story.get("questions") or [],
            }

        story_id = prior_story.get("id") or prior_story.get("story_id")
        if story_id:
            match = next((item for item in STORY_BANK if item["id"] == story_id), None)
            if match:
                return {"id": match["id"], "story": match["story"], "questions": match["questions"]}

        if prior_story.get("story"):
            match = next((item for item in STORY_BANK if item["story"] == prior_story["story"]), None)
            if match:
                return {"id": match["id"], "story": match["story"], "questions": match["questions"]}

    if prior_story and isinstance(prior_story, str):
        match = next((item for item in STORY_BANK if item["story"] == prior_story), None)
        if match:
            return {"id": match["id"], "story": match["story"], "questions": match["questions"]}

    return _unused(STORY_BANK, set())


def assign_sets(used_story_ids=None, used_memory_ids=None, used_speech_ids=None, preferred_story_id=None):
    story = next((item for item in STORY_BANK if item["id"] == preferred_story_id), None) if preferred_story_id else None
    if story is None:
        story = _unused(STORY_BANK, set(used_story_ids or []))
    memory = _unused(MEMORY_BANK, set(used_memory_ids or []))
    used_speech = set(used_speech_ids or [])
    speech = _unused(SPEECH_BANK, used_speech)
    return {
        "story": {"id": story["id"], "story": story["story"], "questions": story["questions"]},
        "memory": memory,
        "speech": {**speech, "options": [speech]},
    }


def scheduled_date(started_at, session_number):
    # Schedule by the calendar day shown to the user, while MongoDB keeps UTC timestamps.
    local_start_date = started_at.astimezone().date() if started_at.tzinfo else started_at.date()
    return (local_start_date + timedelta(days=SESSION_OFFSETS[session_number])).isoformat()


def reminder_date(started_at, session_number):
    return scheduled_date(started_at, session_number)


def build_cycle_schedule(started_at=None):
    started_at = started_at or datetime.now(timezone.utc)
    return [{
        "session_number": number,
        "scheduled_for": scheduled_date(started_at, number),
        "reminder_for": reminder_date(started_at, number),
        "status": "scheduled",
    } for number in (1, 2, 3)]


def trend(scores):
    values = [score for score in scores if score is not None]
    if len(values) < 2:
        return {"values": values, "direction": "insufficient_data", "change": 0}
    change = round(values[-1] - values[0], 2)
    return {"values": values, "direction": "improving" if change > 0 else "declining" if change < 0 else "stable", "change": change}