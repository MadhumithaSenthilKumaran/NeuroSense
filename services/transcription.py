"""
Compatibility wrapper: expose transcribe() under services.transcription
by delegating to the existing top-level transcription.py helper.
"""
try:
    from transcription import transcribe as transcribe_impl
except Exception:
    transcribe_impl = None


def transcribe(audio_path: str):
    """Delegate to the top-level transcription.transcribe if available,
    otherwise mimic the lightweight behavior (return None) and log a warning
    when running under a Flask app context.
    """
    if transcribe_impl:
        return transcribe_impl(audio_path)

    # Fallback: if running inside Flask, warn and return None (lightweight behavior)
    try:
        from flask import current_app
        current_app.logger.warning("transcription implementation not importable; returning None (lightweight fallback)")
    except Exception:
        pass
    return None
