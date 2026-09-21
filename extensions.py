from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import time

jwt = JWTManager()
_client = None
_db = None


def _with_database(uri, database="neurosense"):
    scheme_end = uri.find("://")
    if scheme_end < 0:
        return uri
    authority_end = uri.find("/", scheme_end + 3)
    query_start = uri.find("?", scheme_end + 3)
    if authority_end < 0 or (query_start >= 0 and query_start < authority_end):
        insert_at = query_start if query_start >= 0 else len(uri)
        return f"{uri[:insert_at]}/{database}{uri[insert_at:]}"
    if uri[authority_end:authority_end + 2] == "/?" or uri[authority_end:] == "/":
        return f"{uri[:authority_end]}/{database}{uri[authority_end + 1:]}"
    return uri


def init_db(app):
    global _client, _db

    configured = app.config.get("MONGO_URI")
    if not configured:
        raise RuntimeError("MONGO_URI must be configured; refusing to use a local MongoDB fallback")
    candidate_uris = [configured]

    last_error = None
    for raw_uri in candidate_uris:
        uri = _with_database(raw_uri)
        for attempt in range(3):
            try:
                _client = MongoClient(uri, serverSelectionTimeoutMS=15000, connectTimeoutMS=10000)
                _db = _client.get_default_database()
                _db.command("ping")
                app.config["MONGO_URI"] = uri
                break
            except Exception as exc:  # pragma: no cover - depends on Atlas availability
                last_error = exc
                if _client is not None:
                    _client.close()
                _client = None
                _db = None
                if attempt < 2:
                    time.sleep(1)
        if _db is not None:
            break
    else:
        detail = str(last_error)
        if isinstance(last_error, ServerSelectionTimeoutError) and "DNS" in detail:
            detail = (
                "MongoDB Atlas hostname could not be resolved. Check internet/DNS access, "
                "the Atlas cluster hostname in MONGO_URI, and VPN/firewall settings."
            )
        raise RuntimeError(f"Could not connect to MongoDB Atlas: {detail}") from last_error

    # Indexes — created idempotently on startup.
    _db.users.create_index("email", unique=True)
    _db.assessments.create_index("user_id")
    _db.assessments.create_index(
        [("user_id", 1), ("cycle_id", 1), ("session_number", 1)],
        unique=True,
        partialFilterExpression={"cycle_id": {"$exists": True}, "session_number": {"$exists": True}},
    )
    _db.assessment_cycles.create_index([("user_id", 1), ("cycle_id", 1)], unique=True, sparse=True)
    _db.reports.create_index("assessment_id")
    return _db


def get_db():
    if _db is None:
        raise RuntimeError("Database not initialized — call init_db(app) first.")
    return _db