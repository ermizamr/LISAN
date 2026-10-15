"""Configuration for LISAN Telegram Bot."""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_TUPLES_PATH = BASE_DIR / "landing" / "data" / "community_tuples.json"
LOCAL_USER_STATS_PATH = Path(__file__).resolve().parent / "user_stats.json"

# Telegram Bot Token (set via environment variable or replace here)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Supabase Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xknxnycwrkffmxcwqxjs.supabase.co")
SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhrbnhueWN3cmtmZm14Y3dxeGpzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIwODM5MTQsImV4cCI6MjEwNzY1OTkxNH0.5MgXgdhAtUggyNnCpL94EcjmR5JrAs74fiYK0BjUDaM",
)

# Supported Languages
LANGUAGES = {
    "amh": {"name": "Amharic", "native": "አማርኛ", "flag": "🇪🇹"},
    "orm": {"name": "Afaan Oromoo", "native": "Afaan Oromoo", "flag": "🌳"},
    "tir": {"name": "Tigrinya", "native": "ትግርኛ", "flag": "🇪🇷"},
    "som": {"name": "Somali", "native": "Soomaali", "flag": "🇸🇴"},
    "eng": {"name": "English", "native": "English", "flag": "🇬🇧"},
}

# Domains & Icons
DOMAIN_ICONS = {
    "medical": "🏥 Medical & Triage",
    "idioms": "💡 Authentic Idioms",
    "commerce": "💳 Commerce & Market",
    "transit": "🚕 Transit & Direction",
    "civic": "🏛️ Civic & Legal",
    "grammar_conjugation": "📚 Grammar Conjugation",
    "daily_conversation": "🗣️ Daily Conversation",
    "general": "🌐 General",
}
