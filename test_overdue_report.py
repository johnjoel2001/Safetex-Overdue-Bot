#!/usr/bin/env python3
"""Test script — fetches overdue invoices and sends the report to Telegram immediately."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from zoho_agent import get_access_token
from overdue_report import get_overdue_invoices, categorize_overdue, format_summary, generate_pdf
import datetime


async def main():
    import telegram

    bot_token = os.getenv("TELEGRAM_OVERDUE_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print("🔑 Getting Zoho access token...")
    token = get_access_token()

    print("📥 Fetching overdue invoices...")
    invoices = get_overdue_invoices(token)

    print("🗂  Categorizing...")
    categorized = categorize_overdue(invoices)

    summary = format_summary(categorized)
    print("\n" + "=" * 60)
    print("SUMMARY MESSAGE:")
    print("=" * 60)
    print(summary)
    print("=" * 60 + "\n")

    from telegram.request import HTTPXRequest

    print("📤 Sending to Telegram...")
    request = HTTPXRequest(read_timeout=30, connect_timeout=15, write_timeout=30)
    bot = telegram.Bot(token=bot_token, request=request)

    async with bot:
        await bot.send_message(chat_id=chat_id, text=summary, parse_mode="Markdown")
        print("  ✓ Sent summary message")

        total_count = sum(len(v) for v in categorized.values())
        if total_count > 0:
            print("📄 Generating PDF...")
            pdf_buf = generate_pdf(categorized)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            await bot.send_document(
                chat_id=chat_id,
                document=pdf_buf,
                filename=f"Overdue_Report_{today_str}.pdf",
                caption="📎 Detailed breakdown attached",
            )
            print("  ✓ Sent PDF document")

    print("✅ Report sent successfully! (summary + PDF)")


if __name__ == "__main__":
    asyncio.run(main())
