import os
from datetime import time
import pytz
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

from whatsapp_report import send_whatsapp_report

load_dotenv()

IST = pytz.timezone("Asia/Kolkata")


def job():
    print("📊 Running scheduled WhatsApp overdue report...")
    send_whatsapp_report()


def main():
    scheduler = BackgroundScheduler(timezone=IST)
    scheduler.add_job(job, "cron", hour=9, minute=0)
    scheduler.start()

    print("📊 WhatsApp overdue report bot is running...")
    print("⏰ Report scheduled daily at 9:00 AM IST")

    # Run once immediately if requested
    if os.getenv("WHATSAPP_RUN_NOW", "0") == "1":
        print("🏃 Running once now (WHATSAPP_RUN_NOW=1)...")
        job()

    try:
        while True:
            import time as _time
            _time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
