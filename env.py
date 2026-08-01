import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
ORG_ID = os.getenv("ZOHO_ORG_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GREEN_API_INSTANCE_ID = os.getenv("GREEN_API_INSTANCE_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
WHATSAPP_GROUP_ID = os.getenv("WHATSAPP_GROUP_ID")
