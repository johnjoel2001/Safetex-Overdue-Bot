import os
import time
import schedule
import pytz
from dotenv import load_dotenv

from whatsapp_report import send_whatsapp_report

load_dotenv()

IST = pytz.timezone("Asia/Kolkata")


def job():
    print("📊 Running scheduled WhatsApp overdue report...")
    send_whatsapp_report()


def main():
    schedule.every().day.at("09:00").do(job)

    print("📊 WhatsApp overdue report bot is running...")
    print("⏰ Report scheduled daily at 9:00 AM IST")

    # Run once immediately if requested
    if os.getenv("WHATSAPP_RUN_NOW", "0") == "1":
        print("🏃 Running once now (WHATSAPP_RUN_NOW=1)...")
        job()

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
