from flask import Flask

from extensions import init_db
from services import notification_service


def make_app():
    app = Flask(__name__)
    app.config.update(
        SMTP_HOST="smtp.example.test",
        SMTP_PORT=587,
        SMTP_USERNAME="user",
        SMTP_PASSWORD="password",
        SMTP_FROM_EMAIL="no-reply@example.test",
        FRONTEND_URL="http://localhost:5173",
    )
    return app


def test_unconfigured_db_is_left_empty_and_non_fatal(monkeypatch):
    seen = {}

    class DummyCollection:
        def create_index(self, *args, **kwargs):
            return None

    class DummyDB:
        def __init__(self):
            self.users = DummyCollection()
            self.assessments = DummyCollection()
            self.assessment_cycles = DummyCollection()
            self.reports = DummyCollection()

        def command(self, *args, **kwargs):
            return {"ok": 1}

        def create_index(self, *args, **kwargs):
            return None

    class DummyClient:
        def __init__(self, uri, **kwargs):
            seen["uri"] = uri

        def get_default_database(self):
            return DummyDB()

        def close(self):
            return None

    monkeypatch.setattr("extensions.MongoClient", DummyClient)
    app = Flask(__name__)
    app.config["MONGO_URI"] = ""

    db = init_db(app)

    assert app.config["MONGO_URI"] == ""
    assert "MONGO_WARNING" in app.config
    assert db is None


def test_init_db_is_non_fatal_when_mongo_unavailable(monkeypatch):
    def fail_connect(*args, **kwargs):
        raise RuntimeError("database offline")

    monkeypatch.setattr("extensions.MongoClient", fail_connect)
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb+srv://example:test@cluster.example.mongodb.net/?appName=Cluster0"

    db = init_db(app)

    assert db is None
    assert app.config["MONGO_WARNING"].startswith("MongoDB unavailable")


def test_email_enabled_sends(monkeypatch):
    sent = []
    monkeypatch.setattr(notification_service, "send_email", lambda *args: sent.append(args))
    with make_app().app_context():
        result = notification_service.send_assessment_notification({
            "email": "person@example.com", "email_notifications": True,
        })
    assert sent
    assert result == {"email_notification_status": "sent"}


def test_email_disabled_is_skipped(monkeypatch):
    monkeypatch.setattr(notification_service, "send_email", lambda *args: (_ for _ in ()).throw(AssertionError()))
    with make_app().app_context():
        result = notification_service.send_assessment_notification({
            "email": "person@example.com", "email_notifications": False,
        })
    assert result == {"email_notification_status": "skipped"}


def test_invalid_email_is_safe(monkeypatch):
    monkeypatch.setattr(notification_service, "send_email", lambda *args: (_ for _ in ()).throw(AssertionError()))
    with make_app().app_context():
        result = notification_service.send_assessment_notification({
            "email": "not-an-email", "email_notifications": True,
        })
    assert result == {"email_notification_status": "failed"}


def test_provider_failure_does_not_raise(monkeypatch):
    monkeypatch.setattr(notification_service, "send_email", lambda *args: (_ for _ in ()).throw(RuntimeError("offline")))
    with make_app().app_context():
        result = notification_service.send_assessment_notification({
            "email": "person@example.com", "email_notifications": True,
        })
    assert result == {"email_notification_status": "failed"}