from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional
import html
import logging
import os
import platform

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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

def _fmt_money(v: Any) -> str:
    try:
        return f"{float(v):,.2f}".replace(",", " ").replace(".00", ".00")
    except Exception:
        return "0.00"


def _ru_date(iso_date: str) -> str:
    """
    Преобразует YYYY-MM-DD -> DD.MM.YYYY.
    Если формат другой — возвращает как есть (без падения).
    """
    if not iso_date:
        return ""
    s = str(iso_date).strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}.{s[5:7]}.{s[0:4]}"
    return s


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    safe = html.escape(text or "").replace("\n", "<br/>")
    return Paragraph(safe, style)

def _p_rich(rich_text: str, style: ParagraphStyle) -> Paragraph:
    """
    Paragraph с reportlab-markup (<b>, <br/>) без экранирования.
    Важно: rich_text должен быть уже безопасным (вставки пользователя предварительно html.escape()).
    """
    return Paragraph(rich_text or "", style)


def generate_contract_pdf_from_data(contract: Dict[str, Any]) -> bytes:
    """
    Генерирует "профессиональный" PDF договора из структурных данных конструктора.
    Ориентир: читаемо и аккуратно (заголовки, таблицы, подписи, 2 колонки сторон).
    """
    title = (contract.get("title") or "ДОГОВОР").strip()
    meta = contract.get("meta") or {}
    number = str(meta.get("number") or "").strip()
    city = str(meta.get("city") or "").strip() or "г. ________"
    sign_date = _ru_date(str(meta.get("signDate") or "").strip()) or "«___» __________ 20__ г."
    parties = contract.get("parties") or {}
    party_a = (parties.get("a") or {})
    party_b = (parties.get("b") or {})
    subject = contract.get("subject") or {}
    items = subject.get("items") or []

    start_date = _ru_date(subject.get("startDate") or "")
    end_date = _ru_date(subject.get("endDate") or "")
    term_days = subject.get("termDays") or 0
    total = subject.get("total") or 0

    payment = contract.get("payment") or {}
    pay_type = (payment.get("type") or "").strip()

    options = contract.get("options") or {}

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=48,
        title=title or "Contract",
        author="DocScan AI",
    )

    styles = getSampleStyleSheet()

    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=15.5,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=12,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=6,
    )
    normal = ParagraphStyle(
        "NormalRU",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=10.5,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    small = ParagraphStyle(
        "SmallRU",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=9.5,
        leading=12.5,
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    story: List[Any] = []
    story.append(_p(title, h1))
    if number:
        story.append(_p(f"№ {number}", ParagraphStyle("Num", parent=small, alignment=TA_CENTER, spaceAfter=6)))

    # Шапка: город слева, дата справа
    header_tbl = Table(
        [[_p(city, small), _p(sign_date, small)]],
        colWidths=[doc.width * 0.5, doc.width * 0.5],
    )
    header_tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(header_tbl)
    story.append(Spacer(1, 6))

    # 1. Стороны (2 колонки)
    story.append(_p("1. Стороны", h2))

    def party_block(p: Dict[str, Any], fallback_name: str) -> str:
        name = (p.get("name") or "").strip() or fallback_name
        inn = (p.get("inn") or "").strip()
        ogrn = (p.get("ogrn") or "").strip()
        address = (p.get("address") or "").strip()
        rep = (p.get("rep") or "").strip()
        basis = (p.get("basis") or "").strip()
        lines = [f"<b>{html.escape(name)}</b>"]
        if inn:
            lines.append(f"ИНН: {html.escape(inn)}")
        if ogrn:
            lines.append(f"ОГРН/ОГРНИП: {html.escape(ogrn)}")
        if address:
            lines.append(f"Адрес: {html.escape(address)}")
        if rep:
            lines.append(f"Представитель: {html.escape(rep)}")
        if basis:
            lines.append(f"Основание: {html.escape(basis)}")
        return "<br/>".join(lines)

    parties_tbl = Table(
        [
            [
                _p_rich(f"<b>Сторона 1</b><br/>{party_block(party_a, 'Сторона 1')}", small),
                _p_rich(f"<b>Сторона 2</b><br/>{party_block(party_b, 'Сторона 2')}", small),
            ]
        ],
        colWidths=[doc.width * 0.5, doc.width * 0.5],
    )
    parties_tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#e9ecef")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(parties_tbl)
    story.append(_p("1.1. Стороны заключили настоящий договор на условиях, изложенных ниже.", normal))

    # 2. Предмет
    story.append(_p("2. Предмет договора", h2))
    story.append(_p("2.1. Сторона 1 обязуется исполнить обязательства по настоящему договору, а Сторона 2 — принять результат и оплатить его на условиях договора.", normal))

    # Таблица позиций
    if items:
        rows = [["№", "Наименование", "Кол-во", "Цена, руб.", "Сумма, руб."]]
        total_calc = 0.0
        for idx, it in enumerate(items, 1):
            title_it = str(it.get("title") or "").strip()
            qty = float(it.get("qty") or 0)
            price = float(it.get("price") or 0)
            line_sum = max(0.0, qty) * max(0.0, price)
            total_calc += line_sum
            rows.append([str(idx), title_it or "—", str(int(qty) if qty.is_integer() else qty), _fmt_money(price), _fmt_money(line_sum)])

        tbl = Table(
            rows,
            colWidths=[doc.width * 0.06, doc.width * 0.46, doc.width * 0.12, doc.width * 0.18, doc.width * 0.18],
            hAlign="LEFT",
        )
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8f9fa")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#212529")),
                    ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                    ("FONTSIZE", (0, 0), (-1, 0), 9.5),
                    ("FONTNAME", (0, 1), (-1, -1), FONT_REGULAR),
                    ("FONTSIZE", (0, 1), (-1, -1), 9.5),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (2, 1), (4, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e9ecef")),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                    ("TOPPADDING", (0, 1), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                ]
            )
        )
        story.append(tbl)
        story.append(Spacer(1, 6))

        # Итого справа
        total_tbl = Table(
            [[_p("Итого:", small), _p_rich(f"<b>{html.escape(_fmt_money(total_calc if total_calc else total))} руб.</b>", small)]],
            colWidths=[doc.width * 0.75, doc.width * 0.25],
        )
        total_tbl.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, 0), "RIGHT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(total_tbl)
    else:
        story.append(_p("2.2. Перечень работ/услуг/товаров согласуется Сторонами дополнительно.", normal))

    # 3. Сроки
    story.append(_p("3. Сроки", h2))
    story.append(_p(f"3.1. Дата начала: {start_date or '________'}. Срок выполнения: {term_days or '___'} дней.", normal))
    story.append(_p(f"3.2. Дата окончания (расчётная): {end_date or '________'}.", normal))

    # 4. Цена
    story.append(_p("4. Цена договора", h2))
    story.append(_p(f"4.1. Общая стоимость по договору составляет { _fmt_money(total) } руб.", normal))

    # 5. Оплата
    story.append(_p("5. Порядок оплаты", h2))
    if pay_type == "prepay30":
        story.append(_p("5.1. Оплата производится на условиях предоплаты 30% и последующей постоплаты 70%.", normal))
    elif pay_type == "postpay":
        story.append(_p("5.1. Оплата производится после исполнения обязательств и подписания подтверждающих документов.", normal))
    elif pay_type == "equal":
        story.append(_p("5.1. Оплата производится равными платежами по согласованному графику.", normal))
    else:
        story.append(_p("5.1. Порядок оплаты определяется соглашением Сторон.", normal))

    # 6-8. Опции
    if options.get("acceptanceAct"):
        story.append(_p("6. Приёмка и акт", h2))
        story.append(_p("6.1. По факту исполнения Стороны подписывают акт приёмки.", normal))
    if options.get("warranty12"):
        story.append(_p("7. Гарантия", h2))
        story.append(_p("7.1. Гарантийный срок составляет 12 (двенадцать) месяцев.", normal))
    if options.get("confidentiality"):
        story.append(_p("8. Конфиденциальность", h2))
        story.append(_p("8.1. Стороны обязуются сохранять конфиденциальность информации, полученной в рамках договора.", normal))

    # 9-12. Стандартные условия (чтобы договор был "полным")
    story.append(_p("9. Ответственность", h2))
    story.append(_p("9.1. Стороны несут ответственность за неисполнение или ненадлежащее исполнение обязательств по договору в соответствии с законодательством Российской Федерации.", normal))
    story.append(_p("9.2. Уплата штрафных санкций не освобождает Стороны от исполнения обязательств.", normal))

    story.append(_p("10. Форс-мажор", h2))
    story.append(_p("10.1. Стороны освобождаются от ответственности за частичное или полное неисполнение обязательств, если оно явилось следствием обстоятельств непреодолимой силы (форс-мажор).", normal))
    story.append(_p("10.2. Сторона, для которой наступили такие обстоятельства, обязана уведомить другую Сторону в разумный срок.", normal))

    story.append(_p("11. Разрешение споров", h2))
    story.append(_p("11.1. Споры и разногласия решаются путем переговоров. При недостижении соглашения спор подлежит рассмотрению в суде в порядке, установленном законодательством РФ.", normal))

    story.append(_p("12. Заключительные положения", h2))
    story.append(_p("12.1. Договор вступает в силу с даты подписания и действует до полного исполнения обязательств Сторонами.", normal))
    story.append(_p("12.2. Все изменения и дополнения действительны при оформлении в письменном виде и подписании обеими Сторонами.", normal))

    # 13. Реквизиты (банк) — чтобы выглядело профессионально
    def requisites_rows(p: Dict[str, Any]) -> List[List[Any]]:
        def g(k: str) -> str:
            return str(p.get(k) or "").strip()
        rows = []
        if g("bank"):
            rows.append(["Банк", g("bank")])
        if g("rs"):
            rows.append(["Р/с", g("rs")])
        if g("ks"):
            rows.append(["К/с", g("ks")])
        if g("bik"):
            rows.append(["БИК", g("bik")])
        return rows

    story.append(_p("13. Реквизиты", h2))
    req_a = requisites_rows(party_a)
    req_b = requisites_rows(party_b)
    if req_a or req_b:
        # таблица 2 колонки: слева реквизиты стороны 1, справа стороны 2
        def req_table_block(req_rows: List[List[Any]]) -> Paragraph:
            if not req_rows:
                return _p("—", small)
            lines = [f"{html.escape(k)}: {html.escape(v)}" for k, v in req_rows]
            return _p_rich("<br/>".join(lines), small)

        req_tbl = Table(
            [[
                _p_rich(f"<b>Сторона 1</b><br/>{req_table_block(req_a).text}", small),
                _p_rich(f"<b>Сторона 2</b><br/>{req_table_block(req_b).text}", small),
            ]],
            colWidths=[doc.width * 0.5, doc.width * 0.5],
        )
        req_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6)]))
        story.append(req_tbl)

    # 9. Подписи (2 колонки)
    story.append(_p("14. Подписи Сторон", h2))

    left_name = (party_a.get("name") or "Сторона 1").strip() or "Сторона 1"
    right_name = (party_b.get("name") or "Сторона 2").strip() or "Сторона 2"
    left_name_safe = html.escape(left_name)
    right_name_safe = html.escape(right_name)
    sig_left = f"<b>{left_name_safe}</b><br/><br/>____________________ /_____________/"
    sig_right = f"<b>{right_name_safe}</b><br/><br/>____________________ /_____________/"
    sig_tbl = Table(
        [
            [
                _p_rich(sig_left, small),
                _p_rich(sig_right, small),
            ]
        ],
        colWidths=[doc.width * 0.5, doc.width * 0.5],
    )
    sig_tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(sig_tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


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

