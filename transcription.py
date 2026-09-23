"""
Speech-to-text wrapper.

- If LIGHTWEIGHT_MODE=false and faster-whisper is installed, real Whisper
  transcription runs on CPU or GPU.
- Otherwise (default, so the app runs out-of-the-box) this returns None and
  the frontend simply skips transcript-dependent display (word-for-word
  accuracy). Acoustic features (pitch, MFCC, pause duration, etc.) are
  always computed for real regardless of this flag — see speech_features.py.

To enable real transcription:
  pip install faster-whisper
  set LIGHTWEIGHT_MODE=false
"""

from flask import current_app

_model_cache = {}


def transcribe(audio_path: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        current_app.logger.warning(
            "faster-whisper not installed; skipping transcription. "
            "Run `pip install faster-whisper` and set LIGHTWEIGHT_MODE=false."
        )
        return None

    lightweight = current_app.config.get("LIGHTWEIGHT_MODE", False)
    if lightweight:
        current_app.logger.info(
            "LIGHTWEIGHT_MODE is enabled, but transcription is still available because faster-whisper is installed."
        )

    size = current_app.config["WHISPER_MODEL_SIZE"]
    if size not in _model_cache:
        _model_cache[size] = WhisperModel(size, device="cpu", compute_type="int8")
    model = _model_cache[size]

    segments, _info = model.transcribe(
        audio_path,
        beam_size=5,
        language="en",
        task="transcribe",
        condition_on_previous_text=False,
        vad_filter=True,
        temperature=0.0,
    )
    transcript = " ".join(
        seg.text.strip() for seg in segments if seg.text and seg.text.strip()
    ).strip()
    return transcript or None