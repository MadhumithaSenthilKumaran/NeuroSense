"""
Wrapper exposing build_report_pdf under services.pdf_report by delegating
to the top-level pdf_report.py module.
"""
try:
    from pdf_report import build_report_pdf  # noqa: F401
except Exception:
    def build_report_pdf(output_path, user, assessment, lifestyle, cognitive, speech_docs, verification_url):
        # Minimal fallback: create an empty PDF-like placeholder (text file with .pdf extension)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("NeuroSense report placeholder\n")
                f.write(f"Assessment ID: {assessment.get('_id') if isinstance(assessment, dict) else assessment}\n")
        except Exception:
            pass
