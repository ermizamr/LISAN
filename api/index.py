"""LISAN Telegram Bot - Vercel Serverless Webhook Handler.

Receives incoming Telegram updates via HTTPS POST from Telegram webhooks,
processes them with the LISAN application pipeline, and returns 200 OK.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add root directory to sys.path so modules import seamlessly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from telegram import Update
from telegram_bot.bot import create_bot_application


async def process_telegram_update(update_dict: dict):
    """Processes a single Telegram update with full async lifecycle."""
    app = create_bot_application()
    async with app:
        update = Update.de_json(update_dict, app.bot)
        if update:
            await app.process_update(update)


class handler(BaseHTTPRequestHandler):
    """Vercel Python Serverless HTTP Request Handler."""

    def do_GET(self):
        """Health check endpoint to verify webhook availability."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        response_data = {
            "status": "online",
            "system": "LISAN Community Validation Bot",
            "mode": "Serverless Webhook",
            "bot": "@LisanAiEtBot",
            "version": "1.0.3"
        }
        self.wfile.write(json.dumps(response_data, indent=2).encode("utf-8"))

    def do_POST(self):
        """Processes incoming Telegram webhook payloads."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_length)

            if post_body:
                update_dict = json.loads(post_body.decode("utf-8"))
                asyncio.run(process_telegram_update(update_dict))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        except Exception as exc:
            # Return 200 so Telegram does not retry failed updates repeatedly
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error_data = {"ok": False, "error": str(exc)}
            self.wfile.write(json.dumps(error_data).encode("utf-8"))
