"""
Compatibility wrapper: expose send_report_email under services.email_service
by delegating to the existing top-level email_service.py helper.
"""
try:
    from email_service import send_report_email  # noqa: F401
except Exception:
    def send_report_email(to_address, pdf_path, user_name):
        # Fallback: do nothing (SMTP not configured) but keep signature.
        try:
            import logging
            logging.getLogger(__name__).warning("email_service not available; send_report_email is a no-op in this environment")
        except Exception:
            pass
