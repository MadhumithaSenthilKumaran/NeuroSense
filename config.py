import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Central configuration. All secrets are read from environment variables —
    NOTHING is hardcoded. Copy .env.example to .env and fill in real values
    before running in any shared environment.
    """

    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me-please-32")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me-32-bytes!!")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # --- Database ---
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/neurosense")

    # --- CORS ---
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

    # --- File uploads ---
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/tmp/neurosense_uploads")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB audio uploads

    # --- Speech-to-text ---
    # Whisper model size: tiny / base / small / medium / large.
    # "base" is a reasonable CPU-friendly default for a screening tool.
    WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")

    # --- ML model artifact paths ---
    MODEL_DIR = os.environ.get("MODEL_DIR", os.path.join(os.path.dirname(__file__), "artifacts"))
    MODEL_PATH = os.path.join(MODEL_DIR, "xgboost_risk_model.json")
    SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
    FEATURE_LIST_PATH = os.path.join(MODEL_DIR, "feature_list.json")

    # --- Guardian email (SMTP) ---
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", "no-reply@neurosense.app")

    # --- Feature flags ---
    # Real transcription/embedding models are heavy. Default to lightweight
    # mode so the app runs out-of-the-box on a laptop; flip to False once
    # whisper / sentence-transformers are installed and warmed up.
    LIGHTWEIGHT_MODE = os.environ.get("LIGHTWEIGHT_MODE", "true").lower() == "true"