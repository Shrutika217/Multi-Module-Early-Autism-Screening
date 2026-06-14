from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
import json


def generate_pdf(report_text, charts=None, filename="temp/report.pdf"):

    os.makedirs("temp", exist_ok=True)

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # ==============================
    # STYLES
    # ==============================
    main_title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,
        spaceAfter=10,
        leading=22
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.darkblue,
        spaceAfter=6,
        leading=14
    )

    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        spaceAfter=5
    )

    compact_style = ParagraphStyle(
        'Compact',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        spaceAfter=5
    )

    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        leading=11,
        spaceAfter=5
    )

    content = []

    # ==============================
    # TITLE
    # ==============================
    content.append(
        Paragraph(
            "<b>Autism Spectrum Disorder - Initial Screening Results</b>",
            main_title_style
        )
    )
    content.append(Spacer(1, 0.1 * inch))

    # ==============================
    # 🔥 FIXED PATIENT INFO
    # ==============================
    try:
        with open("temp/temp_result.json", "r") as f:
            data = json.load(f)

        demo = data.get("demographics", {})

        raw_gender = str(demo.get("gender", "")).lower()
        if raw_gender in ["m", "male"]:
            gender = "Male"
        elif raw_gender in ["f", "female"]:
            gender = "Female"
        else:
            gender = "Not specified"

        jaundice = "Yes" if demo.get("jaundice") else "No"
        family_asd = "Yes" if demo.get("family_asd") else "No"

        ethnicity = demo.get("ethnicity", "Not specified")
        who_completed = demo.get("who_completed", "Not specified")

        content.append(Paragraph("<b>PATIENT INFORMATION</b>", section_style))
        content.append(Spacer(1, 6))

        content.append(Paragraph(f"Age: {demo.get('age', 'N/A')}", normal_style))
        content.append(Paragraph(f"Gender: {gender}", normal_style))
        content.append(Paragraph(f"Jaundice History: {jaundice}", normal_style))
        content.append(Paragraph(f"Family History of ASD: {family_asd}", normal_style))
        content.append(Paragraph(f"Ethnicity: {ethnicity}", normal_style))
        content.append(Paragraph(f"Form Completed By: {who_completed}", normal_style))

        content.append(Spacer(1, 12))

    except Exception:
        content.append(Paragraph("Patient information unavailable", normal_style))
        content.append(Spacer(1, 12))

    # ==============================
    # OPTIONAL: CHARTS
    # ==============================
    if charts:
        content.append(Paragraph("<b>VISUAL ANALYSIS</b>", section_style))
        content.append(Spacer(1, 6))

        try:
            content.append(Paragraph("Autism Probability", normal_style))
            content.append(Image(charts["probability"], width=400, height=120))
            content.append(Spacer(1, 10))

            content.append(Paragraph("Behavioral Traits", normal_style))
            content.append(Image(charts["traits"], width=300, height=300))
            content.append(Spacer(1, 10))

            content.append(Paragraph("Modalities Used", normal_style))
            content.append(Image(charts["modalities"], width=300, height=200))
            content.append(Spacer(1, 15))

        except Exception:
            pass

    # ==============================
    # REPORT TEXT (FIXED BLOCK SKIP)
    # ==============================
    lines = report_text.split("\n")

    skip_patient_block = False

    for line in lines:
        line = line.strip()

        if not line:
            content.append(Spacer(1, 0.08 * inch))
            continue

        # 🔥 START SKIPPING PATIENT BLOCK
        if "PATIENT INFORMATION" in line.upper():
            skip_patient_block = True
            continue

        # 🔥 STOP SKIPPING WHEN NEXT SECTION STARTS
        if skip_patient_block and "LEVEL" in line.upper():
            skip_patient_block = False

        if skip_patient_block:
            continue

        # ==============================
        # NORMAL RENDERING
        # ==============================
        elif line.isupper() and len(line) < 60:
            content.append(Paragraph(f"<b>{line}</b>", section_style))

        elif "disclaimer" in line.lower():
            content.append(Paragraph(f"<b>{line}</b>", disclaimer_style))

        elif len(line) > 180:
            content.append(Paragraph(line, compact_style))

        else:
            content.append(Paragraph(line, normal_style))

    doc.build(content)

    return filename