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

def main():
    app = ApplicationBuilder().token(OVERDUE_BOT_TOKEN).build()

    # Telegram daily report
    app.job_queue.run_daily(
        send_overdue_report,
        time=time(9, 0, 0, tzinfo=IST),
    )

    # WhatsApp daily report (same process — Railway runs one service)
    wa_scheduler = BackgroundScheduler(timezone=IST)
    wa_scheduler.add_job(
        send_whatsapp_report,
        "cron",
        hour=9,
        minute=0,
    )
    wa_scheduler.start()

    print("📊 Overdue report bot is running...")
    print("⏰ Telegram + WhatsApp scheduled daily at 9:00 AM IST")
    app.run_polling()


if __name__ == "__main__":
    main()
