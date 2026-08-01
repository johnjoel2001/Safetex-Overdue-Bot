#!/usr/bin/env python3
"""Helper script — lists all WhatsApp chats/groups so you can find the group ID."""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

GREEN_API_BASE = "https://api.green-api.com"


def main():
    instance_id = os.getenv("GREEN_API_INSTANCE_ID")
    token = os.getenv("GREEN_API_TOKEN")

    if not instance_id or not token:
        print("❌ Set GREEN_API_INSTANCE_ID and GREEN_API_TOKEN in .env first")
        sys.exit(1)

    url = f"{GREEN_API_BASE}/waInstance{instance_id}/getChats/{token}"
    print("📥 Fetching chats from Green API...\n")

    resp = requests.get(url)
    resp.raise_for_status()
    chats = resp.json()

    groups = []
    for chat in chats:
        chat_id = chat.get("id", "")
        if "@g.us" in chat_id:
            name = chat.get("name", "(no name)")
            groups.append((chat_id, name))

    if not groups:
        print("No groups found. Make sure your WhatsApp account is in a group.")
        return

    print("Found WhatsApp groups:\n")
    for chat_id, name in groups:
        print(f"  Group: {name}")
        print(f"  ID:    {chat_id}")
        print()

    print("Add the group ID to your .env as WHATSAPP_GROUP_ID")


if __name__ == "__main__":
    main()
