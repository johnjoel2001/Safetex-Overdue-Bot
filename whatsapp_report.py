import os
import io
import datetime
import requests

from overdue_report import (
    get_overdue_invoices,
    categorize_overdue,
    format_summary,
    generate_pdf,
)


GREEN_API_BASE = "https://api.green-api.com"


def _green_api_url(method):
    instance_id = os.getenv("GREEN_API_INSTANCE_ID")
    token = os.getenv("GREEN_API_TOKEN")
    return f"{GREEN_API_BASE}/waInstance{instance_id}/{method}/{token}"


def send_whatsapp_report():
    """Fetch overdue invoices and send summary + PDF to a WhatsApp group via Green API."""
    from zoho_agent import get_access_token

    group_id = os.getenv("WHATSAPP_GROUP_ID")
    if not group_id:
        print("⚠️  WHATSAPP_GROUP_ID not set in .env — skipping WhatsApp report")
        return

    try:
        token = get_access_token()
        invoices = get_overdue_invoices(token)
        categorized = categorize_overdue(invoices)

        summary = format_summary(categorized)

        # Send summary text message
        resp = requests.post(
            _green_api_url("sendMessage"),
            json={"chatId": group_id, "message": summary},
        )
        resp.raise_for_status()
        print("  ✓ Sent summary message to WhatsApp group")

        total_count = sum(len(v) for v in categorized.values())
        if total_count > 0:
            pdf_buf = generate_pdf(categorized)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            filename = f"Overdue_Report_{today_str}.pdf"

            resp = requests.post(
                _green_api_url("sendFileByUpload"),
                data={
                    "chatId": group_id,
                    "caption": "📎 Detailed breakdown attached",
                },
                files={"file": (filename, pdf_buf, "application/pdf")},
            )
            resp.raise_for_status()
            print("  ✓ Sent PDF document to WhatsApp group")

        print("✅ WhatsApp overdue report sent (summary + PDF)")
    except Exception as e:
        print(f"❌ Failed to send WhatsApp overdue report: {e}")
