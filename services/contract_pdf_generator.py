from __future__ import annotations

from io import BytesIO
from typing import Optional
import html
import logging
import os
import platform

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def _register_cyrillic_fonts() -> None:
    """Пытаемся зарегистрировать системные TTF со встроенной кириллицей."""
    global FONT_REGULAR, FONT_BOLD

    font_paths = {
        "Windows": [
            ("CyrillicRegular", "C:/Windows/Fonts/arial.ttf"),
            ("CyrillicBold", "C:/Windows/Fonts/arialbd.ttf"),
            ("CyrillicRegular", "C:/Windows/Fonts/calibri.ttf"),
            ("CyrillicBold", "C:/Windows/Fonts/calibrib.ttf"),
            ("CyrillicRegular", "C:/Windows/Fonts/times.ttf"),
            ("CyrillicBold", "C:/Windows/Fonts/timesbd.ttf"),
        ],
        "Linux": [
            ("CyrillicRegular", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            ("CyrillicBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            ("CyrillicRegular", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            ("CyrillicBold", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        ],
        "Darwin": [
            ("CyrillicRegular", "/Library/Fonts/Arial.ttf"),
            ("CyrillicBold", "/Library/Fonts/Arial Bold.ttf"),
        ],
    }

    system = platform.system()
    candidates = font_paths.get(system, font_paths["Linux"])

    regular_ok = False
    bold_ok = False

    for font_name, path in candidates:
        if not os.path.exists(path):
            continue
        try:
            if font_name == "CyrillicRegular" and not regular_ok:
                pdfmetrics.registerFont(TTFont("CyrillicRegular", path))
                regular_ok = True
            if font_name == "CyrillicBold" and not bold_ok:
                pdfmetrics.registerFont(TTFont("CyrillicBold", path))
                bold_ok = True
        except Exception as e:
            logger.warning(f"Не удалось зарегистрировать шрифт {path}: {e}")

        if regular_ok and bold_ok:
            break

    if regular_ok:
        FONT_REGULAR = "CyrillicRegular"
    if bold_ok:
        FONT_BOLD = "CyrillicBold"


_register_cyrillic_fonts()


def generate_contract_pdf(*, title: str, text: str) -> bytes:
    """
    Генерирует PDF договора из plain-text (с переносами строк).

    Важно: `text` должен быть уже финальным текстом договора (с включёнными секциями).
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
        title=title or "Contract",
        author="DocScan AI",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ContractTitle",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=14,
    )
    body_style = ParagraphStyle(
        "ContractBody",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=10.8,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )

    story = []
    safe_title = html.escape(title or "Договор")
    story.append(Paragraph(safe_title, title_style))
    story.append(Spacer(1, 6))

    # Разбиваем на абзацы по пустым строкам. Внутри абзаца переводы строк -> <br/>
    raw = (text or "").strip()
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = ["(пустой документ)"]

    for p in paragraphs:
        safe = html.escape(p).replace("\n", "<br/>")
        story.append(Paragraph(safe, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

