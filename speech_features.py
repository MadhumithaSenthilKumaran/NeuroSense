"""
Acoustic feature extraction for the Speech Assessment module.

All features listed in the spec are computed directly from the uploaded/
recorded audio with librosa — nothing here is mocked. Speech-to-text
(for reading-accuracy / pause-detection refinement) is handled separately
in services/transcription.py and is the one piece that is stubbed unless
faster-whisper is installed (see LIGHTWEIGHT_MODE in config.py).
"""

import numpy as np
import librosa


def _pause_duration_seconds(y, sr, top_db=30):
    """Estimate total silence/pause duration using librosa's silence split."""
    intervals = librosa.effects.split(y, top_db=top_db)
    voiced = sum((end - start) for start, end in intervals) / sr
    total = len(y) / sr
    return max(total - voiced, 0.0)


def _speech_rate_wpm(transcript, duration_s):
    if not transcript or duration_s <= 0:
        return None
    words = len(transcript.split())
    minutes = duration_s / 60.0
    return round(words / minutes, 1) if minutes > 0 else None


def extract_features(audio_path: str, transcript: str = None) -> dict:
    """
    Load an audio file and compute the full acoustic feature set:
    MFCC, pitch, speech rate, energy, pause duration, spectral centroid,
    zero crossing rate, chroma, spectral roll-off.
    """
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    duration_s = len(y) / sr if sr else 0

    # MFCC (13 coefficients, mean + std across time)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = mfcc.mean(axis=1).tolist()
    mfcc_std = mfcc.std(axis=1).tolist()

    # Pitch (fundamental frequency) via pyin
    try:
        f0, voiced_flag, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7")
        )
        voiced_f0 = f0[~np.isnan(f0)]
        pitch_hz = float(np.mean(voiced_f0)) if len(voiced_f0) else None
    except Exception:
        pitch_hz = None

    # Energy (RMS)
    rms = librosa.feature.rms(y=y)[0]
    energy = float(np.mean(rms))

    # Pause duration
    pause_duration_s = float(_pause_duration_seconds(y, sr))

    # Spectral centroid
    spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))

    # Zero crossing rate
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))

    # Chroma
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = float(np.mean(chroma))

    # Spectral roll-off
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))

    speech_rate_wpm = _speech_rate_wpm(transcript, duration_s)

    return {
        "duration_s": round(duration_s, 2),
        "mfcc_mean": [round(v, 4) for v in mfcc_mean],
        "mfcc_std": [round(v, 4) for v in mfcc_std],
        "pitch_hz": round(pitch_hz, 2) if pitch_hz else None,
        "speech_rate_wpm": speech_rate_wpm,
        "energy": round(energy, 5),
        "pause_duration_s": round(pause_duration_s, 2),
        "pause_rate": round(pause_duration_s / duration_s, 4) if duration_s else 0.0,
        "spectral_centroid": round(spectral_centroid, 2),
        "zero_crossing_rate": round(zcr, 5),
        "chroma_mean": round(chroma_mean, 4),
        "spectral_rolloff": round(rolloff, 2),
    }


def waveform_points(audio_path: str, target_points: int = 400):
    """Downsample the waveform to ~target_points for frontend plotting."""
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    if len(y) == 0:
        return []
    step = max(1, len(y) // target_points)
    downsampled = y[::step]
    return [round(float(v), 4) for v in downsampled]