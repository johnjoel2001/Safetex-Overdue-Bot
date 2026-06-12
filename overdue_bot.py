import os
from datetime import time
import pytz
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from overdue_report import send_overdue_report

load_dotenv()

OVERDUE_BOT_TOKEN = os.getenv("TELEGRAM_OVERDUE_BOT_TOKEN")
IST = pytz.timezone("Asia/Kolkata")


def main():
    app = ApplicationBuilder().token(OVERDUE_BOT_TOKEN).build()

    # Schedule daily overdue report at 9:00 AM IST
    app.job_queue.run_daily(
        send_overdue_report,
        time=time(9, 0, 0, tzinfo=IST),
    )

    print("📊 Overdue report bot is running...")
    print("⏰ Report scheduled daily at 9:00 AM IST")
    app.run_polling()


if __name__ == "__main__":
    main()
