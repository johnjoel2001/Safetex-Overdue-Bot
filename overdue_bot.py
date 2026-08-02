import os
from datetime import time
import pytz
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.background import BackgroundScheduler
from overdue_report import send_overdue_report
from whatsapp_report import send_whatsapp_report

load_dotenv()

OVERDUE_BOT_TOKEN = os.getenv("TELEGRAM_OVERDUE_BOT_TOKEN")
IST = pytz.timezone("Asia/Kolkata")

# TEST time — change back to 9:00 after verification
TEST_HOUR = 12
TEST_MINUTE = 5


def main():
    app = ApplicationBuilder().token(OVERDUE_BOT_TOKEN).build()

    # Telegram daily report
    app.job_queue.run_daily(
        send_overdue_report,
        time=time(TEST_HOUR, TEST_MINUTE, 0, tzinfo=IST),
    )

    # WhatsApp daily report (same process — Railway runs one service)
    wa_scheduler = BackgroundScheduler(timezone=IST)
    wa_scheduler.add_job(
        send_whatsapp_report,
        "cron",
        hour=TEST_HOUR,
        minute=TEST_MINUTE,
    )
    wa_scheduler.start()

    print("📊 Overdue report bot is running...")
    print(f"⏰ Telegram + WhatsApp scheduled daily at {TEST_HOUR:02d}:{TEST_MINUTE:02d} IST (TEST)")
    app.run_polling()


if __name__ == "__main__":
    main()
