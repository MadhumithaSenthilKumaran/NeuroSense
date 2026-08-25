from flask_jwt_extended import JWTManager
from pymongo import MongoClient

jwt = JWTManager()
_client = None
_db = None


def init_db(app):
    global _client, _db
    _client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=5000)
    _db = _client.get_default_database()
    # Indexes — created idempotently on startup.
    _db.users.create_index("email", unique=True)
    _db.assessments.create_index("user_id")
    _db.reports.create_index("assessment_id")
    return _db


def get_db():
    if _db is None:
        raise RuntimeError("Database not initialized — call init_db(app) first.")
    return _db