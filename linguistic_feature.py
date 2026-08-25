"""
Computes the same linguistic-complexity features the speech sub-model was
trained on (see ml/train_speech_model.py), from a live transcript. This is
what lets the trained model actually be used at inference time instead of
only on the original training CSV.

Requires a transcript, which requires transcription.py to have run in
non-lightweight mode (faster-whisper installed). If no transcript is
available, returns None and the caller should skip the speech sub-model
score and fall back to acoustic-only features.
"""

import math
import re

FILLER_WORDS = {
    "um", "uh", "er", "ah", "hmm", "erm", "like", "you know", "i mean",
    "well", "so", "actually", "basically", "literally",
}


def _tokenize(text: str):
    return re.findall(r"[A-Za-z']+", text.lower())


def _sentences(text: str):
    parts = re.split(r"[.!?]+", text)
    return [p.strip() for p in parts if p.strip()]


def _moving_average_ttr(tokens, window=10):
    if len(tokens) < window:
        window = max(1, len(tokens))
    if window == 0:
        return 0.0
    ratios = []
    for i in range(0, len(tokens) - window + 1):
        chunk = tokens[i:i + window]
        ratios.append(len(set(chunk)) / len(chunk))
    return sum(ratios) / len(ratios) if ratios else 0.0


def _brunets_index(n_tokens, n_types):
    # Brunet's W = N^(V^-0.165); lower W = higher lexical richness.
    if n_tokens == 0 or n_types == 0:
        return 0.0
    return round(n_tokens ** (n_types ** -0.165), 3)


def _repetition_count(tokens):
    reps = 0
    for i in range(1, len(tokens)):
        if tokens[i] == tokens[i - 1]:
            reps += 1
    return reps


def extract_linguistic_features(transcript: str, duration_s: float = None) -> dict:
    if not transcript or not transcript.strip():
        return None

    text_lower = transcript.lower()
    tokens = _tokenize(transcript)
    sentences = _sentences(transcript)

    filler_count = sum(text_lower.count(fw) for fw in FILLER_WORDS)
    token_count = len(tokens)
    type_count = len(set(tokens))
    type_token_ratio = round(type_count / token_count, 4) if token_count else 0.0
    ma_ttr = round(_moving_average_ttr(tokens), 4)
    brunets_index = _brunets_index(token_count, type_count)

    # Content density: proportion of content (non-function) words.
    # Lightweight heuristic stopword list — a full POS tagger would be more
    # accurate but adds a heavy NLP dependency for a screening prototype.
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "and", "or", "but",
        "to", "of", "in", "on", "at", "for", "with", "it", "this", "that",
        "i", "we", "you", "he", "she", "they", "then", "there", "as", "be",
        "been", "being", "so", "very", "just", "did", "do", "does",
    }
    content_words = [t for t in tokens if t not in stopwords]
    content_density = round(len(content_words) / token_count, 4) if token_count else 0.0

    repetitions = _repetition_count(tokens)
    sentence_count = max(1, len(sentences))
    average_words_per_sentence = round(token_count / sentence_count, 2)

    return {
        "filler_count": filler_count,
        "token_count": token_count,
        "type_count": type_count,
        "type_token_ratio": type_token_ratio,
        "ma_ttr": ma_ttr,
        "brunets_index": brunets_index,
        "content_density": content_density,
        "repetitions": repetitions,
        "sentence_count": sentence_count,
        "average_words_per_sentence": average_words_per_sentence,
        "total_seconds": round(duration_s, 1) if duration_s else 0.0,
    }