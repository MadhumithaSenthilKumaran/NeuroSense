import logging
import re
import smtplib
from email.message import EmailMessage

from flask import current_app


logger = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
REPORT_MESSAGE = (
    "Your NeuroSense preliminary assessment has been completed and your report is now available.\n\n"
    "Please log in to your NeuroSense account to view your cognitive-risk assessment, contributing factors, and explanation.\n\n"
    "NeuroSense provides preliminary cognitive-risk information for awareness and screening purposes. It is not a medical diagnosis.\n\n"
    "If you have concerns about your cognitive health, please consult a qualified healthcare professional."
)


def is_valid_email(value):
    return bool(value and EMAIL_RE.fullmatch(value.strip()))


def send_email(to_email, subject, message):
    """Send a plain-text email using the application's SMTP configuration."""
    if not is_valid_email(to_email):
        raise ValueError("Invalid email address")
    cfg = current_app.config
    if not cfg["SMTP_HOST"] or not cfg["SMTP_USERNAME"] or not cfg["SMTP_PASSWORD"]:
        raise RuntimeError("SMTP is not configured")

    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = cfg["SMTP_FROM_EMAIL"]
    email["To"] = to_email.strip()
    email.set_content(message)
    with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=20) as server:
        server.starttls()
        server.login(cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"])
        server.send_message(email)


def send_assessment_notification(user):
    """Send the report email without allowing delivery errors to escape."""
    statuses = {"email_notification_status": "skipped"}
    if user.get("email_notifications", True):
        if not is_valid_email(user.get("email")):
            statuses["email_notification_status"] = "failed"
            logger.error("Email notification failed: invalid recipient")
        else:
            try:
                report_url = current_app.config["FRONTEND_URL"].rstrip("/") + "/reports"
                send_email(
                    user["email"],
                    "NeuroSense Assessment Report Available",
                    f"{REPORT_MESSAGE}\n\nView your report: {report_url}",
                )
                statuses["email_notification_status"] = "sent"
            except Exception as error:
                statuses["email_notification_status"] = "failed"
                logger.error("Email notification failed: %s", error)

    return statuses


def send_session_day_notification(user, session_number, scheduled_for):
    """Notify the user when a scheduled session becomes available today."""
    if not user.get("email_notifications", True) or not is_valid_email(user.get("email")):
        return "skipped"
    try:
        send_email(
            user["email"],
            f"NeuroSense Session {session_number} Is Available",
            f"Your NeuroSense Session {session_number} is available today ({scheduled_for}).\n\n"
            "Please log in to your NeuroSense account to continue your assessment.\n\n"
            "NeuroSense provides preliminary cognitive-risk information for awareness and screening purposes. "
            "It is not a medical diagnosis.",
        )
        return "sent"
    except Exception as error:
        logger.error("Session-day email notification failed: %s", error)
        return "failed"
