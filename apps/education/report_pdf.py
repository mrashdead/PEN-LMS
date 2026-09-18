"""Persian PDF builder for learner/parent report cards."""
from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, XPreformatted,
)

from apps.core.utils import persian_date, persian_numbers

_RESHAPER = arabic_reshaper.ArabicReshaper(
    {"delete_harakat": False, "support_ligatures": True}
)


def _rtl_line(value) -> str:
    return get_display(_RESHAPER.reshape(str(value)))


def _rtl_paragraph(value, style, width):
    lines = []
    for logical_line in str(value).split("\n"):
        words = [w for w in re.split(r"\s+", logical_line.strip()) if w]
        current = []
        for word in words:
            attempt = " ".join(current + [word])
            if current and pdfmetrics.stringWidth(
                _RESHAPER.reshape(attempt), style.fontName, style.fontSize
            ) > width:
                lines.append(_rtl_line(" ".join(current)))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(_rtl_line(" ".join(current)))
    return XPreformatted("\n".join(escape(line) for line in lines), style)


def _register_fonts() -> tuple[str, str]:
    regular = "VazirPDF"
    bold = "VazirPDF-Bold"
    if regular in pdfmetrics.getRegisteredFontNames():
        return regular, bold
    root = Path(__file__).resolve().parents[2]
    font_dir = root / "frontend" / "Admin" / "src" / "assets" / "fonts" / "Vazir"
    regular_path = font_dir / "Vazir-Regular-FD.ttf"
    bold_path = font_dir / "Vazir-Bold-FD.ttf"
    if not regular_path.exists():
        raise RuntimeError("فونت فارسی PDF در پروژه پیدا نشد.")
    pdfmetrics.registerFont(TTFont(regular, str(regular_path)))
    pdfmetrics.registerFont(TTFont(bold, str(bold_path if bold_path.exists() else regular_path)))
    return regular, bold


def build_learner_report_pdf(*, student, attendance: dict, report_cards: list[dict]) -> bytes:
    """Build a compact, readable A4 report for a student/parent."""
    regular, bold = _register_fonts()
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="گزارش آموزشی دانش‌آموز",
        author="Pen LMS",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "fa-title", parent=styles["Title"], fontName=bold, fontSize=17,
        leading=27, alignment=TA_RIGHT, textColor=colors.HexColor("#244b68"),
    )
    heading = ParagraphStyle(
        "fa-heading", parent=styles["Heading2"], fontName=bold, fontSize=12,
        leading=21, alignment=TA_RIGHT, textColor=colors.HexColor("#244b68"),
    )
    body = ParagraphStyle(
        "fa-body", parent=styles["BodyText"], fontName=regular, fontSize=9.5,
        leading=17, alignment=TA_RIGHT, textColor=colors.HexColor("#28323c"),
    )
    small = ParagraphStyle(
        "fa-small", parent=body, fontSize=8.5, leading=15,
        textColor=colors.HexColor("#5b6874"),
    )

    name = f"{student.first_name} {student.last_name}".strip()
    totals = attendance.get("totals") or {}
    story = [
        Paragraph(_rtl_line("گزارش آموزشی دانش‌آموز"), title),
        Spacer(1, 4 * mm),
        Table(
            [[
                Paragraph(_rtl_line(f"دانش‌آموز: {name}"), body),
                Paragraph(_rtl_line(f"کد دانش‌آموزی: {student.student_code or '—'}"), body),
            ]],
            colWidths=[90 * mm, 75 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef5f8")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c6d8e0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]),
        ),
        Spacer(1, 6 * mm),
        Paragraph(_rtl_line("خلاصهٔ حضور و غیاب"), heading),
        Spacer(1, 2 * mm),
        Table(
            [[
                _rtl_line(f"حضور مؤثر: {persian_numbers(attendance.get('rate', 0))}٪"),
                _rtl_line(f"حضور به‌موقع: {persian_numbers(attendance.get('on_time_rate', 0))}٪"),
                _rtl_line(f"جلسات ثبت‌شده: {persian_numbers(attendance.get('all', 0))}"),
            ], [
                _rtl_line(f"حاضر: {persian_numbers(totals.get('present', 0))}"),
                _rtl_line(f"تأخیر: {persian_numbers(totals.get('late', 0))}"),
                _rtl_line(f"غایب / موجه: {persian_numbers(totals.get('absent', 0))} / {persian_numbers(totals.get('excused', 0))}"),
            ]],
            colWidths=[55 * mm, 55 * mm, 55 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f7f9")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8dee4")),
                ("FONTNAME", (0, 0), (-1, -1), regular),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]),
        ),
        Spacer(1, 6 * mm),
        Paragraph(_rtl_line("کارنامهٔ توصیفی"), heading),
        Spacer(1, 2 * mm),
    ]
    if report_cards:
        rows = [[_rtl_line("درس / برگزاری"), _rtl_line("نتیجه"), _rtl_line("یادداشت مدرس")]]
        for card in report_cards:
            lesson = card.get("lesson") or card.get("offering") or "—"
            rows.append([
                _rtl_line(lesson),
                _rtl_line(card.get("result_display") or card.get("result") or "—"),
                _rtl_line(card.get("teacher_note") or "—"),
            ])
        story.append(Table(
            rows, colWidths=[50 * mm, 30 * mm, 85 * mm], repeatRows=1,
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#244b68")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), bold),
                ("FONTNAME", (0, 1), (-1, -1), regular),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8dee4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7f9")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]),
        ))
    else:
        story.append(Paragraph(_rtl_line("هنوز کارنامه‌ای برای این دانش‌آموز صادر نشده است."), body))
    story.extend([
        Spacer(1, 8 * mm),
        Paragraph(_rtl_line(f"تاریخ تهیه: {persian_date(None)}"), small),
        Paragraph(_rtl_line("این گزارش از اطلاعات ثبت‌شده در سامانهٔ Pen LMS تهیه شده است."), small),
    ])
    doc.build(story)
    return buffer.getvalue()
