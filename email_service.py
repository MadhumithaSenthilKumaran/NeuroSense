import smtplib
from email.message import EmailMessage
from flask import current_app


def send_report_email(to_email: str, pdf_path: str, patient_name: str):
    cfg = current_app.config
    msg = EmailMessage()
    msg["Subject"] = f"NeuroSense Screening Report for {patient_name}"
    msg["From"] = cfg["SMTP_FROM"]
    msg["To"] = to_email
    msg.set_content(
        f"Attached is the NeuroSense preliminary risk screening report for {patient_name}.\n\n"
        "This is a screening/awareness tool only and is not a medical diagnosis. "
        "Please consult a qualified healthcare professional for any concerns."
    )
    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="NeuroSense_Report.pdf")

    with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"]) as server:
        server.starttls()
        server.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
        server.send_message(msg)


def send_session_reminder(to_email: str, patient_name: str, session_number: int, scheduled_for: str):
    cfg = current_app.config
    msg = EmailMessage()
    msg["Subject"] = f"NeuroSense Session {session_number} reminder"
    msg["From"] = cfg["SMTP_FROM"]
    msg["To"] = to_email
    msg.set_content(
        f"Hello {patient_name},\n\n"
        f"Your NeuroSense Session {session_number} is scheduled for {scheduled_for}. "
        "You will be able to start it on that date from your report.\n\n"
        "NeuroSense is a screening and awareness tool, not a medical diagnosis."
    )
    with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"]) as server:
        server.starttls()
        server.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
        server.send_message(msg)