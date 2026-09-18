"""Generates a real PDF chain-of-custody report for a case, using reportlab.

This is one of the few frontend "buttons" that gets a genuinely functional
backend implementation end-to-end: click Generate Report -> server builds an
actual PDF from live DB data -> frontend downloads it.
"""
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import settings
from app.models import Case


def build_case_report(case: Case) -> Path:
    out_path = settings.REPORTS_DIR / f"{case.number}.pdf"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "NVTitle", parent=styles["Title"], fontSize=18, spaceAfter=4
    )
    meta_style = ParagraphStyle(
        "NVMeta", parent=styles["Normal"], textColor=colors.HexColor("#555555")
    )

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title=f"NyayVault Evidence Report — {case.number}",
    )

    story = [
        Paragraph("NyayVault — Digital Evidence Report", title_style),
        Paragraph(f"{case.number} &mdash; {case.title}", styles["Heading2"]),
        Paragraph(
            f"Case status: <b>{case.status.value.upper()}</b> &nbsp;|&nbsp; "
            f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}",
            meta_style,
        ),
        Spacer(1, 10 * mm),
        Paragraph("Evidence Items", styles["Heading3"]),
    ]

    table_data = [["Name", "Type", "Uploader", "Uploaded", "Status", "SHA-256"]]
    for d in case.documents:
        table_data.append(
            [
                Paragraph(d.name, styles["Normal"]),
                d.type.value,
                d.uploader.full_name if d.uploader else "—",
                d.uploaded_at.strftime("%d %b %Y %H:%M") if d.uploaded_at else "—",
                d.status.value,
                Paragraph(d.hash_sha256, styles["Code"] if "Code" in styles else styles["Normal"]),
            ]
        )

    if len(table_data) == 1:
        story.append(Paragraph("No evidence has been uploaded to this case yet.", styles["Normal"]))
    else:
        tbl = Table(table_data, repeatRows=1, colWidths=[95, 40, 65, 60, 50, 160])
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12233d")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6f8")]),
                ]
            )
        )
        story.append(tbl)

    story.append(Spacer(1, 10 * mm))
    story.append(
        Paragraph(
            "This report is system-generated from the chain-of-custody records held "
            "by NyayVault at the time of generation. Hash values reflect the state "
            "recorded at upload and/or the most recent integrity check.",
            meta_style,
        )
    )

    doc.build(story)
    return out_path
