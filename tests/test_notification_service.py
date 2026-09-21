from flask import Flask

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