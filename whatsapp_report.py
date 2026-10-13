import os
import io
import time
import datetime
import requests

from overdue_report import (
    get_overdue_invoices,
    categorize_overdue,
    format_summary,
    generate_pdf,
)


# Seconds to wait between attempts (~33 min total) — Green API has had multi-minute 5xx outages
RETRY_DELAYS = [60, 120, 300, 600, 900]


def _green_api_base():
    # Green API serves each instance from https://{first 4 digits}.api.greenapi.com;
    # the legacy api.green-api.com host is no longer reliably reachable.
    instance_id = os.getenv("GREEN_API_INSTANCE_ID", "")
    return os.getenv("GREEN_API_URL") or f"https://{instance_id[:4]}.api.greenapi.com"


def _green_api_url(method):
    instance_id = os.getenv("GREEN_API_INSTANCE_ID")
    token = os.getenv("GREEN_API_TOKEN")
    return f"{_green_api_base().rstrip('/')}/waInstance{instance_id}/{method}/{token}"


def _redact(msg):
    token = os.getenv("GREEN_API_TOKEN")
    return str(msg).replace(token, "***") if token else str(msg)


def _post(method, **kwargs):
    for attempt, delay in enumerate(RETRY_DELAYS + [None], start=1):
        try:
            resp = requests.post(_green_api_url(method), timeout=(15, 120), **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            if delay is None:
                raise
            print(f"  ↻ {method} attempt {attempt} failed ({_redact(e)}), retrying in {delay}s...")
            time.sleep(delay)
            if "files" in kwargs:
                for _, f in kwargs["files"].items():
                    f[1].seek(0)


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
        _post("sendMessage", json={"chatId": group_id, "message": summary})
        print("  ✓ Sent summary message to WhatsApp group")

        total_count = sum(len(v) for v in categorized.values())
        if total_count > 0:
            pdf_buf = generate_pdf(categorized)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            filename = f"Overdue_Report_{today_str}.pdf"

            _post(
                "sendFileByUpload",
                data={
                    "chatId": group_id,
                    "caption": "📎 Detailed breakdown attached",
                },
                files={"file": (filename, pdf_buf, "application/pdf")},
            )
            print("  ✓ Sent PDF document to WhatsApp group")

        print("✅ WhatsApp overdue report sent (summary + PDF)")
    except Exception as e:
        print(f"❌ Failed to send WhatsApp overdue report: {_redact(e)}")
