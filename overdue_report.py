import os
import io
import datetime
import requests
import pytz
from env import ORG_ID

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

IST = pytz.timezone("Asia/Kolkata")

# Buckets processed in order — first match wins
BUCKETS = [
    (">60 days", lambda d: d > 60),
    (">30 days", lambda d: d > 30),
    (">15 days", lambda d: d > 15),
    (">7 days",  lambda d: d > 7),
    ("5 days",   lambda d: d >= 5),
    ("3 days",   lambda d: d >= 3),
    ("1 day",    lambda d: d >= 1),
]

BUCKET_ICONS = {
    ">60 days": "🔴",
    ">30 days": "🟠",
    ">15 days": "🟡",
    ">7 days":  "🟢",
    "5 days":   "🔵",
    "3 days":   "🔷",
    "1 day":    "⚪",
}


def get_overdue_invoices(token):
    url = "https://www.zohoapis.in/books/v3/invoices"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    all_invoices = []
    page = 1

    while True:
        params = {
            "organization_id": ORG_ID,
            "status": "overdue",
            "per_page": 200,
            "page": page,
        }
        res = requests.get(url, params=params, headers=headers)
        res.raise_for_status()
        invoices = res.json().get("invoices", [])
        if not invoices:
            break
        all_invoices.extend(invoices)
        if len(invoices) < 200:
            break
        page += 1

    print(f"📥 Fetched {len(all_invoices)} overdue invoice(s) from Zoho")
    return all_invoices


def categorize_overdue(invoices):
    today = datetime.date.today()
    categorized = {label: [] for label, _ in BUCKETS}

    for inv in invoices:
        due_date_str = inv.get("due_date")
        if not due_date_str:
            continue
        due_date = datetime.date.fromisoformat(due_date_str)
        days_overdue = (today - due_date).days
        if days_overdue <= 0:
            continue

        for label, check in BUCKETS:
            if check(days_overdue):
                categorized[label].append({**inv, "days_overdue": days_overdue})
                break

    return categorized


DIV = "─" * 30

BUCKET_COLORS = {
    ">60 days": colors.HexColor("#E74C3C"),
    ">30 days": colors.HexColor("#E67E22"),
    ">15 days": colors.HexColor("#F1C40F"),
    ">7 days":  colors.HexColor("#2ECC71"),
    "5 days":   colors.HexColor("#3498DB"),
    "3 days":   colors.HexColor("#2980B9"),
    "1 day":    colors.HexColor("#95A5A6"),
}


def format_summary(categorized):
    """Returns just the summary message text for Telegram."""
    today_str = datetime.date.today().strftime("%d %b %Y")

    total_amount = sum(
        float(inv.get("balance", 0))
        for invoices in categorized.values()
        for inv in invoices
    )
    total_count = sum(len(v) for v in categorized.values())

    summary_lines = [
        f"🗓  *{today_str}*",
        "",
        f"💰 *Total Overdue:*  ₹{total_amount:,.2f}",
        f"📋 *Total Invoices:*  {total_count}",
        "",
        DIV,
        "*Bucket Summary*",
        DIV,
    ]
    for label, invoices in categorized.items():
        if not invoices:
            continue
        icon = BUCKET_ICONS.get(label, "•")
        bucket_total = sum(float(inv.get("balance", 0)) for inv in invoices)
        summary_lines.append(
            f"{icon}  {label:<10}  {len(invoices):>2} inv   ₹{bucket_total:>12,.2f}"
        )
    summary_lines.append(DIV)

    if total_count == 0:
        return "📊 *DAILY OVERDUE REPORT*\n\n✅ *No overdue invoices today!* Great work."

    return "📊 *DAILY OVERDUE REPORT*\n\n" + "\n".join(summary_lines)


def generate_pdf(categorized):
    """Generates a detailed overdue report PDF and returns it as a bytes buffer."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=18, spaceAfter=4 * mm, textColor=colors.HexColor("#2C3E50"),
    )
    date_style = ParagraphStyle(
        "DateLine", parent=styles["Normal"],
        fontSize=11, textColor=colors.grey, spaceAfter=6 * mm, alignment=TA_CENTER,
    )
    bucket_style = ParagraphStyle(
        "BucketHeader", parent=styles["Heading2"],
        fontSize=13, spaceBefore=6 * mm, spaceAfter=3 * mm,
        textColor=colors.HexColor("#2C3E50"),
    )
    cell_style = ParagraphStyle(
        "Cell", parent=styles["Normal"],
        fontSize=9, leading=12,
    )
    cell_right = ParagraphStyle(
        "CellRight", parent=cell_style, alignment=TA_RIGHT,
    )

    today_str = datetime.date.today().strftime("%d %b %Y")
    elements = [
        Paragraph("Daily Overdue Report — Detailed Breakdown", title_style),
        Paragraph(today_str, date_style),
    ]

    col_widths = [28 * mm, 70 * mm, 38 * mm, 28 * mm]

    for label, invoices in categorized.items():
        if not invoices:
            continue

        bucket_color = BUCKET_COLORS.get(label, colors.grey)
        bucket_total = sum(float(inv.get("balance", 0)) for inv in invoices)
        elements.append(
            Paragraph(
                f"{label.upper()} OVERDUE &nbsp;—&nbsp; {len(invoices)} invoice(s) &nbsp;•&nbsp; Rs.{bucket_total:,.2f}",
                bucket_style,
            )
        )

        hdr_style = ParagraphStyle("HdrCell", parent=cell_style, fontName="Helvetica-Bold")
        hdr_right = ParagraphStyle("HdrRight", parent=cell_right, fontName="Helvetica-Bold")
        header_data = [
            [Paragraph("Invoice #", hdr_style),
             Paragraph("Customer", hdr_style),
             Paragraph("Balance (Rs.)", hdr_right),
             Paragraph("Days", hdr_right)],
        ]
        for inv in sorted(invoices, key=lambda x: x["days_overdue"], reverse=True):
            header_data.append([
                Paragraph(inv["invoice_number"], cell_style),
                Paragraph(inv["customer_name"], cell_style),
                Paragraph(f"Rs.{float(inv['balance']):,.2f}", cell_right),
                Paragraph(str(inv["days_overdue"]), cell_right),
            ])

        table = Table(header_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), bucket_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ("LINEBELOW", (0, 0), (-1, 0), 1, bucket_color),
            ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 2 * mm))

    doc.build(elements)
    buf.seek(0)
    return buf


async def send_overdue_report(context):
    from zoho_agent import get_access_token

    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        print("⚠️  TELEGRAM_CHAT_ID not set in .env — skipping report")
        return

    try:
        token = get_access_token()
        invoices = get_overdue_invoices(token)
        categorized = categorize_overdue(invoices)

        summary = format_summary(categorized)
        await context.bot.send_message(chat_id=chat_id, text=summary, parse_mode="Markdown")

        total_count = sum(len(v) for v in categorized.values())
        if total_count > 0:
            pdf_buf = generate_pdf(categorized)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            await context.bot.send_document(
                chat_id=chat_id,
                document=pdf_buf,
                filename=f"Overdue_Report_{today_str}.pdf",
                caption="📎 Detailed breakdown attached",
            )

        print("✅ Overdue report sent (summary + PDF)")
    except Exception as e:
        print(f"❌ Failed to send overdue report: {e}")
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Failed to generate overdue report:\n{e}"
            )
        except Exception:
            pass
