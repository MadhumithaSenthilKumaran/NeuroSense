"""
Generates the downloadable PDF report for a completed assessment:
patient info, assessment date, speech analysis, cognitive results,
lifestyle summary, risk score, SHAP explanation, recommendations, doctor
disclaimer, and a QR code (linking back to the online report/verification
page).
"""

import io
import os
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

TEAL = colors.HexColor("#0F766E")
BLUE = colors.HexColor("#1D4ED8")
LIGHT_BG = colors.HexColor("#F0FDFA")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("NSTitle", parent=styles["Title"], textColor=BLUE, fontSize=22))
    styles.add(ParagraphStyle("NSHeading", parent=styles["Heading2"], textColor=TEAL, spaceBefore=14))
    styles.add(ParagraphStyle("NSBody", parent=styles["BodyText"], fontSize=10, leading=14))
    styles.add(ParagraphStyle("NSDisclaimer", parent=styles["BodyText"], fontSize=9,
                               textColor=colors.HexColor("#7F1D1D"), leading=12))
    return styles


def _qr_image(payload: str, size_mm=30):
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0F766E", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Image(buf, width=size_mm * mm, height=size_mm * mm)


def build_report_pdf(output_path: str, user: dict, assessment: dict,
                      lifestyle: dict, cognitive: dict, speech_docs: list,
                      verification_url: str):
    styles = _styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=20 * mm, bottomMargin=18 * mm)
    story = []

    story.append(Paragraph("NeuroSense", styles["NSTitle"]))
    story.append(Paragraph("Preliminary Alzheimer's Risk Screening Report", styles["Heading3"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "NeuroSense is intended only for preliminary Alzheimer's risk screening and awareness. "
        "It is NOT a medical diagnostic tool and should not replace professional clinical evaluation.",
        styles["NSDisclaimer"],
    ))
    story.append(Spacer(1, 12))

    # Patient info table
    patient_rows = [
        ["Name", user.get("name", "-")],
        ["Age", str(user.get("age", "-"))],
        ["Gender", str(user.get("gender", "-"))],
        ["Education", str(user.get("education", "-"))],
        ["Assessment Date", str(assessment.get("completed_at", "-"))[:19].replace("T", " ")],
    ]
    t = Table(patient_rows, colWidths=[45 * mm, 100 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(Paragraph("Patient Information", styles["NSHeading"]))
    story.append(t)

    # Risk score
    story.append(Paragraph("Overall Risk Assessment", styles["NSHeading"]))
    risk_class = assessment.get("risk_class", "-")
    risk_prob = assessment.get("risk_probability")
    risk_pct = f"{round(risk_prob * 100, 1)}%" if risk_prob is not None else "-"
    story.append(Paragraph(f"<b>Risk Class:</b> {risk_class} &nbsp;&nbsp; <b>Risk Probability:</b> {risk_pct}",
                            styles["NSBody"]))

    modality_scores = assessment.get("modality_scores", {})
    if modality_scores:
        mod_rows = [["Modality", "Score"]] + [
            [k.capitalize(), f"{round(v * 100, 1)}%"] for k, v in modality_scores.items()
        ]
        mt = Table(mod_rows, colWidths=[70 * mm, 40 * mm])
        mt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(Spacer(1, 6))
        story.append(mt)

    # SHAP explanation
    story.append(Paragraph("Explainable AI — Top Contributing Factors", styles["NSHeading"]))
    shap_features = assessment.get("shap_top_features", [])
    if shap_features:
        rows = [["Factor", "Modality", "Contribution"]]
        for f in shap_features[:8]:
            direction = "+" if f["shap_value"] > 0 else "-"
            rows.append([f["feature"], f["modality"], f"{direction}{abs(f['shap_value']):.3f}"])
        st = Table(rows, colWidths=[70 * mm, 30 * mm, 30 * mm])
        st.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(st)

    recs = assessment.get("recommendations", {})
    if recs.get("explanation"):
        story.append(Spacer(1, 6))
        story.append(Paragraph(recs["explanation"], styles["NSBody"]))

    # Cognitive results
    if cognitive:
        story.append(Paragraph("Cognitive Assessment Results", styles["NSHeading"]))
        rows = [
            ["Memory Recall", f"{cognitive.get('memory_recall', {}).get('score', '-')}"],
            ["Reaction Time", f"{cognitive.get('reaction_time', {}).get('avg_ms', '-')} ms"],
            ["Attention", f"{cognitive.get('attention', {}).get('score', '-')}"],
            ["Visual Memory", f"{cognitive.get('visual_memory', {}).get('score', '-')}"],
            ["Pattern Recognition", f"{cognitive.get('pattern_recognition', {}).get('score', '-')}"],
            ["Orientation", f"{cognitive.get('orientation', {}).get('score', '-')}"],
            ["Overall Cognitive Score", f"{cognitive.get('overall_cognitive_score', '-')}"],
        ]
        ct = Table([["Test", "Score"]] + rows, colWidths=[70 * mm, 40 * mm])
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(ct)

    # Speech analysis
    if speech_docs:
        story.append(Paragraph("Speech Analysis Summary", styles["NSHeading"]))
        rows = [["Task", "Pitch (Hz)", "Speech Rate (wpm)", "Pause (s)"]]
        for sd in speech_docs:
            rows.append([
                sd.get("task", "-"), str(sd.get("pitch_hz", "-")),
                str(sd.get("speech_rate_wpm", "-")), str(sd.get("pause_duration_s", "-")),
            ])
        spt = Table(rows, colWidths=[35 * mm, 35 * mm, 40 * mm, 25 * mm])
        spt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ]))
        story.append(spt)

    # Lifestyle summary
    if lifestyle:
        story.append(Paragraph("Lifestyle Summary", styles["NSHeading"]))
        story.append(Paragraph(
            f"Lifestyle Score: {lifestyle.get('lifestyle_score', '-')} / 100 &nbsp;&nbsp; "
            f"Self-Reported Concern Score: {lifestyle.get('concern_score', '-')} / 100",
            styles["NSBody"],
        ))
        elevated = lifestyle.get("elevated_risk_factors", [])
        if elevated:
            story.append(Paragraph("Elevated factors noted: " + ", ".join(elevated), styles["NSBody"]))

    # Recommendations
    story.append(Paragraph("Personalized Recommendations", styles["NSHeading"]))
    for label, key in [
        ("Diet", "diet_suggestions"), ("Exercise", "exercise_recommendations"),
        ("Sleep", "sleep_recommendations"), ("Memory", "memory_improvement_tips"),
        ("Lifestyle", "lifestyle_recommendations"), ("Medical Consultation", "medical_consultation_guidance"),
    ]:
        items = recs.get(key, [])
        if items:
            story.append(Paragraph(f"<b>{label}:</b>", styles["NSBody"]))
            for item in items:
                story.append(Paragraph(f"&bull; {item}", styles["NSBody"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Doctor's Disclaimer: " + recs.get(
            "disclaimer",
            "This assessment is not a medical diagnosis. Please consult a qualified "
            "neurologist or healthcare professional.",
        ),
        styles["NSDisclaimer"],
    ))

    story.append(Spacer(1, 14))
    story.append(_qr_image(verification_url))
    story.append(Paragraph("Scan to view this report online", styles["NSBody"]))

    doc.build(story)
    return output_path