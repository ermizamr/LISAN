"""Telegram Webhook Management Utility for LISAN Bot.

Usage:
  # Check current webhook status
  python scripts/setup_telegram_webhook.py --info

  # Register a new webhook (e.g., after Vercel deployment)
  python scripts/setup_telegram_webhook.py --url https://your-project.vercel.app/api/webhook

  # Switch back to local long-polling
  python scripts/setup_telegram_webhook.py --delete
"""

import sys
import argparse
import httpx
from pathlib import Path

# Ensure proper encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from telegram_bot.config import TELEGRAM_BOT_TOKEN


def get_webhook_info():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    resp = httpx.get(url, timeout=10.0)
    data = resp.json()
    print("\n--- Telegram Webhook Info ---")
    print(data)
    result = data.get("result", {})
    current_url = result.get("url", "")
    print(f"Current URL: {current_url if current_url else '[None - Long Polling Active]'}")
    print(f"Pending updates: {result.get('pending_update_count', 0)}")
    if result.get("last_error_message"):
        print(f"Last error: {result.get('last_error_message')}")
    print("-----------------------------\n")
    return current_url


def set_webhook(webhook_url: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    payload = {"url": webhook_url}
    resp = httpx.post(url, json=payload, timeout=15.0)
    data = resp.json()
    if data.get("ok"):
        print(f"✅ Webhook successfully set to: {webhook_url}")
    else:
        print(f"❌ Failed to set webhook: {data}")


def delete_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    resp = httpx.post(url, json={"drop_pending_updates": False}, timeout=10.0)
    data = resp.json()
    if data.get("ok"):
        print("✅ Webhook deleted! Bot is now ready for Long-Polling mode.")
    else:
        print(f"❌ Failed to delete webhook: {data}")


def main():
    parser = argparse.ArgumentParser(description="Manage LISAN Telegram Webhook")
    parser.add_argument("--info", action="store_true", help="Display current webhook information")
    parser.add_argument("--url", type=str, help="Public HTTPS URL for the webhook")
    parser.add_argument("--delete", action="store_true", help="Delete the current webhook to enable long-polling")

    args = parser.parse_args()

    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment or telegram_bot/.env")
        sys.exit(1)

    if args.url:
        set_webhook(args.url)
        get_webhook_info()
    elif args.delete:
        delete_webhook()
        get_webhook_info()
    else:
        get_webhook_info()


if __name__ == "__main__":
    main()
