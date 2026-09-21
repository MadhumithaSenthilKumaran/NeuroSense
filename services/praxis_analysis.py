"""Computer-vision analysis for the three-number finger praxis task."""

from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from services.mediapipe_hands import create_hands


NOISE_FLOOR = 0.01
def _finger_states(landmarks, handedness="unknown"):
    points = np.array([(point.x, point.y, point.z) for point in landmarks], dtype=float)
    def joint_angle(first, middle, last):
        first_vector = points[first] - points[middle]
        last_vector = points[last] - points[middle]
        denominator = max(np.linalg.norm(first_vector) * np.linalg.norm(last_vector), 1e-6)
        return float(np.degrees(np.arccos(np.clip(np.dot(first_vector, last_vector) / denominator, -1.0, 1.0))))
    def extended(tip, pip, mcp, dip):
        return joint_angle(mcp, pip, dip) > 145 and joint_angle(pip, dip, tip) > 145 and float(np.linalg.norm(points[tip] - points[0])) > float(np.linalg.norm(points[pip] - points[0])) * 1.03
    thumb_extended = points[4, 0] < points[5, 0]
    states = {
        "thumb": int(thumb_extended),
        "index": int(extended(8, 6, 5, 7)),
        "middle": int(extended(12, 10, 9, 11)),
        "ring": int(extended(16, 14, 13, 15)),
        "pinky": int(extended(20, 18, 17, 19)),
    }
    states["count"] = sum(states.values())
    return states, points


def analyze_praxis_video(video_path: str, prompted_numbers: list[int], test_session_id: str, gesture_start_seconds: float = 11.0, capture_windows=None):
    """Extract one schema-shaped trial per prompted number from a recorded video."""
    cap = cv2.VideoCapture(str(Path(video_path)))
    positions = []
    frames_analyzed = 0
    frames_with_hand = 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = float(fps) if fps and fps > 0 else 30.0
    frame_index = 0
    try:
        hands = create_hands()
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                timestamp = frame_index / fps
                frame_index += 1
                frames_analyzed += 1
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    result = hands.process(rgb)
                    if result.multi_hand_landmarks:
                        frames_with_hand += 1
                        hands_in_frame = []
                        for hand_index, detected_hand in enumerate(result.multi_hand_landmarks[:2]):
                            landmarks = getattr(detected_hand, "landmark", detected_hand)
                            handedness = "unknown"
                            handedness_items = getattr(result, "multi_handedness", [])
                            if handedness_items and hand_index < len(handedness_items):
                                category = getattr(handedness_items[hand_index][0], "category_name", "unknown")
                                handedness = str(category).lower()
                            states, points = _finger_states(landmarks, handedness)
                            hands_in_frame.append({"hand": handedness, "states": states, "points": points})
                        positions.append((timestamp, hands_in_frame))
                except Exception:
                    # A dropped frame must not terminate an otherwise valid capture.
                    continue
        finally:
            hands.close()
    finally:
        cap.release()

    total_time = (frame_index - 1) / fps if frame_index else 0.0
    gesture_positions = [item for item in positions if item[0] >= gesture_start_seconds]
    positions = gesture_positions or positions
    gesture_start_seconds = gesture_positions[0][0] if gesture_positions else 0.0
    if not positions:
        return [_empty_trial(test_session_id, number, total_time, frames_analyzed, frames_with_hand) for number in prompted_numbers]

    gesture_end = positions[-1][0]
    boundaries = np.linspace(gesture_start_seconds, gesture_end or gesture_start_seconds + 1.0, len(prompted_numbers) + 1)
    trials = []
    for index, prompted_number in enumerate(prompted_numbers):
        if capture_windows and index < len(capture_windows):
            start = float(capture_windows[index].get('start_seconds', boundaries[index]))
            end = float(capture_windows[index].get('end_seconds', boundaries[index + 1]))
            window = [item for item in positions if start <= item[0] <= end]
        else:
            window = [item for item in positions if boundaries[index] <= item[0] < boundaries[index + 1] or (index == len(prompted_numbers) - 1 and item[0] <= boundaries[index + 1])]
        window = window or positions
        predictions = [sum(hand["states"]["count"] for hand in item[1]) for item in window]
        detected = int(Counter(predictions).most_common(1)[0][0])
        displacement = np.array([item[1][0]["points"][0] for item in window], dtype=float)
        wrist_delta = np.linalg.norm(np.diff(displacement, axis=0), axis=1) if len(displacement) > 1 else np.array([])
        first_move = next((item[0] for item, delta in zip(window[1:], wrist_delta) if delta > NOISE_FLOOR), window[-1][0])
        tips = np.array([[*item[1][0]["points"][8], *item[1][0]["points"][12]] for item in window], dtype=float)
        jitter = float(np.std(tips, axis=0).mean()) if len(tips) else 0.0
        times = np.array([item[0] - gesture_start_seconds for item in window], dtype=float)
        velocities = np.diff(displacement, axis=0) / np.maximum(np.diff(times)[:, None], 1e-6) if len(displacement) > 1 else np.empty((0, 3))
        velocity_variance = float(np.var(np.linalg.norm(velocities, axis=1))) if len(velocities) else 0.0
        trials.append({
            "test_session_id": str(test_session_id),
            "prompted_number": int(prompted_number),
            "gestured_number_detected": detected,
            "is_correct_match": detected == int(prompted_number),
            "metrics": {
                "motor_latency_seconds": round(float(first_move), 4),
                "total_execution_time_seconds": round(float(window[-1][0] - window[0][0]), 4),
                "spatial_jitter_score": round(jitter, 6),
                "angular_velocity_variance": round(velocity_variance, 6),
                "frames_analyzed": frames_analyzed,
                "frames_with_hand": frames_with_hand,
                "stable_count": detected,
                "hand_counts": _majority_hand_counts(window),
                "finger_states": _majority_finger_states(window),
            },
        })
    return trials


def _majority_hand_counts(window):
    grouped = {}
    for item in window:
        for hand in item[1]:
            grouped.setdefault(hand["hand"], []).append(hand["states"]["count"])
    return [{"hand": label, "count": Counter(values).most_common(1)[0][0]} for label, values in grouped.items()]


def _majority_finger_states(window):
    grouped = {}
    for item in window:
        for hand in item[1]:
            grouped.setdefault(hand["hand"], []).append(hand["states"])
    result = []
    for label, states in grouped.items():
        result.append({"hand": label, **{key: Counter(item[key] for item in states).most_common(1)[0][0] for key in ("thumb", "index", "middle", "ring", "pinky", "count")}})
    return result


def _empty_trial(test_session_id, prompted_number, total_time, frames_analyzed=0, frames_with_hand=0):
    return {
        "test_session_id": str(test_session_id),
        "prompted_number": int(prompted_number),
        "gestured_number_detected": 0,
        "is_correct_match": False,
        "metrics": {
            "motor_latency_seconds": 0.0,
            "total_execution_time_seconds": round(float(total_time), 4),
            "spatial_jitter_score": 0.0,
            "angular_velocity_variance": 0.0,
            "frames_analyzed": frames_analyzed,
            "frames_with_hand": frames_with_hand,
        },
    }