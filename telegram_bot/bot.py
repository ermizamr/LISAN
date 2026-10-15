"""LISAN Telegram Bot.

Features:
1. Micro-task Community Validation (Vote Good, Bad, or Submit Corrections).
2. Live Supabase database synchronization.
3. Contributor Gamification (XP, Levels, Ranks, and Leaderboards).
4. Direct Machine Translation lookup across 5 Horn languages.
5. Live Open Data & Research Scorecards.
"""

import os
import sys
import json
import random
import logging
from pathlib import Path

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Ensure proper encoding and sys.path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from telegram_bot.config import (
    TELEGRAM_BOT_TOKEN,
    DATA_TUPLES_PATH,
    LANGUAGES,
    DOMAIN_ICONS,
)
from telegram_bot.supabase_client import (
    record_validation,
    get_global_stats,
    update_user_score,
    get_leaderboard,
    load_user_gamification,
)

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cache of all 3,421 multi-way tuples
CACHED_TUPLES = []


def load_tuples():
    """Loads all community tuples into memory for rapid serving."""
    global CACHED_TUPLES
    if DATA_TUPLES_PATH.exists():
        try:
            with open(DATA_TUPLES_PATH, "r", encoding="utf-8") as f:
                CACHED_TUPLES = json.load(f)
                logger.info(f"Loaded {len(CACHED_TUPLES):,} tuples for validation.")
        except Exception as e:
            logger.error(f"Error loading tuples: {e}")
            CACHED_TUPLES = []
    return CACHED_TUPLES


def get_random_sentence(preferred_lang: str = None) -> dict:
    """Picks a random sentence candidate from the tuple library."""
    if not CACHED_TUPLES:
        load_tuples()
    if not CACHED_TUPLES:
        return {}

    t = random.choice(CACHED_TUPLES)
    available_langs = ["amh", "orm", "tir", "som"]
    lang = preferred_lang if preferred_lang in available_langs else random.choice(available_langs)

    return {
        "tuple_id": t.get("id"),
        "domain": t.get("domain", "general"),
        "english": t.get("english", ""),
        "lang": lang,
        "target": t.get(lang, ""),
    }


def make_card_text(item: dict) -> str:
    """Formats a clean markdown card for Telegram."""
    lang_info = LANGUAGES.get(item["lang"], {"name": item["lang"], "flag": "🌐"})
    domain_label = DOMAIN_ICONS.get(item["domain"], item["domain"])

    return (
        f"✨ *LISAN Community Validation Card*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ *Domain*: {domain_label}\n"
        f"{lang_info['flag']} *Language*: {lang_info['name']} ({lang_info.get('native', '')})\n\n"
        f"🇬🇧 *English*:\n"
        f"`{item['english']}`\n\n"
        f"{lang_info['flag']} *Translation*:\n"
        f"*{item['target']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 _Is this translation accurate, authentic, and natural?_"
    )


def make_card_keyboard(item: dict) -> InlineKeyboardMarkup:
    """Builds inline action buttons for the validation card."""
    buttons = [
        [
            InlineKeyboardButton("👍 Good / ትክክል", callback_data=f"val_good_{item['lang']}"),
            InlineKeyboardButton("👎 Bad / ስህተት", callback_data=f"val_bad_{item['lang']}"),
        ],
        [
            InlineKeyboardButton("✏️ Suggest Edit", callback_data=f"val_edit_{item['lang']}"),
            InlineKeyboardButton("⏭️ Skip", callback_data=f"val_skip_{item['lang']}"),
        ],
        [
            InlineKeyboardButton("🌐 Switch Language", callback_data="val_lang_picker"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_home"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


# ==========================================
# COMMAND HANDLERS
# ==========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the welcoming main menu."""
    user = update.effective_user
    welcome_text = (
        f"👋 *Selam, {user.first_name}!*\n\n"
        f"🌟 Welcome to *LISAN AI* (ልሳን) — the open-source multilingual AI engine for "
        f"Horn of Africa languages:\n"
        f"• 🇪🇹 *Amharic* (አማርኛ)\n"
        f"• 🌳 *Afaan Oromoo*\n"
        f"• 🇪🇷 *Tigrinya* (ትግርኛ)\n"
        f"• 🇸🇴 *Somali* (Soomaali)\n"
        f"• 🇬🇧 *English*\n\n"
        f"Help us evaluate, correct, and curate authentic datasets for open-source AI models!"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎯 Start Validating (አረጋግጥ)", callback_data="val_start"),
        ],
        [
            InlineKeyboardButton("🌐 Quick Translate", callback_data="menu_translate"),
            InlineKeyboardButton("🏆 Leaderboard & XP", callback_data="menu_leaderboard"),
        ],
        [
            InlineKeyboardButton("📊 Dataset Stats", callback_data="menu_stats"),
            InlineKeyboardButton("ℹ️ About & Open Source", callback_data="menu_about"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            welcome_text, parse_mode="Markdown", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            welcome_text, parse_mode="Markdown", reply_markup=reply_markup
        )


async def validate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct /validate command."""
    await send_new_validation_card(update, context)


async def send_new_validation_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Selects and renders a new validation card."""
    pref_lang = context.user_data.get("preferred_lang")
    item = get_random_sentence(pref_lang)

    if not item:
        msg = "⚠️ No sentences available in the library at this moment."
        if update.callback_query:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    context.user_data["current_item"] = item
    context.user_data["awaiting_edit"] = False

    text = make_card_text(item)
    reply_markup = make_card_keyboard(item)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, parse_mode="Markdown", reply_markup=reply_markup
            )
        except Exception:
            await update.callback_query.message.reply_text(
                text, parse_mode="Markdown", reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=reply_markup
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows global dataset and live Supabase validation statistics."""
    stats = get_global_stats()
    text = (
        f"📊 *LISAN Global Corpus & Validation Scorecard*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Total Bitext Dataset*: `373,276 pairs`\n"
        f"🔀 *Language Directions*: `20 pairs (All 5x4 symmetrical)`\n"
        f"💎 *Gold Multi-Way Tuples*: `3,421 concepts (17,105 sentences)`\n\n"
        f"🌐 *Live Community Consensus (Supabase)*:\n"
        f"• Total Submissions: `{stats['total']:,}`\n"
        f"• Approved by Community: `{stats['approved']:,}`\n"
        f"• Human Corrections (Edits): `{stats['edited']:,}`\n"
        f"• Quarantined / Rejected: `{stats['rejected']:,}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 *Live Hub*: [lisan.ermizamr.tech](https://lisan.ermizamr.tech/validate.html)"
    )

    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_home")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=reply_markup, disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=reply_markup, disable_web_page_preview=True
        )


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays top community contributors and personal score."""
    leaders = get_leaderboard(limit=5)
    uid = str(update.effective_user.id)
    all_stats = load_user_gamification()
    my_stats = all_stats.get(uid, {"points": 0, "rank": "🌱 Apprentice Linguist", "total_reviews": 0})

    text = (
        f"🏆 *LISAN Community Leaderboard*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )

    if leaders:
        for i, u in enumerate(leaders, 1):
            badge = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{badge} *{u['username']}* — `{u['points']} XP` ({u['rank']})\n"
    else:
        text += "_No community reviews submitted yet. Be the first!_\n"

    text += (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Your Profile*:\n"
        f"• Rank: *{my_stats['rank']}*\n"
        f"• Total Points: `{my_stats['points']} XP`\n"
        f"• Reviews Cast: `{my_stats['total_reviews']}`\n\n"
        f"💡 _Tip: Validating gives +10 XP, submitting a corrected translation gives +30 XP!_"
    )

    keyboard = [
        [InlineKeyboardButton("🎯 Earn XP Now", callback_data="val_start")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_home")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=reply_markup
        )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays open-source project info and links."""
    text = (
        f"ℹ️ *About LISAN (ልሳን) AI*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"LISAN is an open-source initiative dedicated to advancing AI for low-resource "
        f"languages of the Horn of Africa.\n\n"
        f"• 📜 *License*: Apache 2.0 (Code) / CC-BY 4.0 (Corpus)\n"
        f"• 🐙 *GitHub*: [github.com/ermizamr/LISAN](https://github.com/ermizamr/LISAN)\n"
        f"• 🌐 *Web Validation Hub*: [lisan.ermizamr.tech](https://lisan.ermizamr.tech/validate.html)\n"
        f"• 🗄️ *Database*: Real-time Supabase PostgreSQL\n"
        f"• 🤖 *Target Models*: NLLB-200 600M / 1.3B, LLaMA-3 LoRA\n"
    )

    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_home")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=reply_markup, disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=reply_markup, disable_web_page_preview=True
        )


# ==========================================
# CALLBACK QUERY HANDLER
# ==========================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes interactive button clicks."""
    query = update.callback_query
    data = query.data
    user = update.effective_user

    # Navigation callbacks
    if data == "menu_home":
        await start_command(update, context)
        return
    elif data == "menu_stats":
        await stats_command(update, context)
        return
    elif data == "menu_leaderboard":
        await leaderboard_command(update, context)
        return
    elif data == "menu_about":
        await about_command(update, context)
        return
    elif data == "val_start":
        await send_new_validation_card(update, context)
        return
    elif data == "val_lang_picker":
        # Render language selection keyboard
        buttons = [
            [
                InlineKeyboardButton("🇪🇹 Amharic", callback_data="set_lang_amh"),
                InlineKeyboardButton("🌳 Afaan Oromoo", callback_data="set_lang_orm"),
            ],
            [
                InlineKeyboardButton("🇪🇷 Tigrinya", callback_data="set_lang_tir"),
                InlineKeyboardButton("🇸🇴 Somali", callback_data="set_lang_som"),
            ],
            [
                InlineKeyboardButton("🎲 All Languages (Random)", callback_data="set_lang_all"),
            ],
            [
                InlineKeyboardButton("🔙 Back to Card", callback_data="val_start"),
            ],
        ]
        await query.answer()
        await query.edit_message_text(
            "🌍 *Select which language you want to review:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return
    elif data.startswith("set_lang_"):
        lang = data.replace("set_lang_", "")
        context.user_data["preferred_lang"] = None if lang == "all" else lang
        lang_title = "All Languages" if lang == "all" else LANGUAGES.get(lang, {}).get("name", lang)
        await query.answer(f"Selected: {lang_title}")
        await send_new_validation_card(update, context)
        return

    # Validation action callbacks
    item = context.user_data.get("current_item")
    if not item:
        await query.answer("Session expired. Loading new sentence...")
        await send_new_validation_card(update, context)
        return

    reviewer_id = f"tg_{user.id}"
    username = user.username or user.first_name

    if data.startswith("val_good_"):
        # Record APPROVED in Supabase
        record_validation(
            tuple_id=item["tuple_id"],
            domain=item["domain"],
            english_text=item["english"],
            target_lang=item["lang"],
            original_target=item["target"],
            validated_text=item["target"],
            status="approved",
            reviewer_id=reviewer_id,
        )
        profile = update_user_score(user.id, username, "approved")
        await query.answer(f"✓ Approved! +10 XP (Total: {profile['points']} XP)")
        await send_new_validation_card(update, context)

    elif data.startswith("val_bad_"):
        # Record REJECTED in Supabase
        record_validation(
            tuple_id=item["tuple_id"],
            domain=item["domain"],
            english_text=item["english"],
            target_lang=item["lang"],
            original_target=item["target"],
            validated_text=None,
            status="rejected",
            reviewer_id=reviewer_id,
        )
        profile = update_user_score(user.id, username, "rejected")
        await query.answer(f"✓ Rejected & Quarantined! +10 XP (Total: {profile['points']} XP)")
        await send_new_validation_card(update, context)

    elif data.startswith("val_skip_"):
        await query.answer("Skipped")
        await send_new_validation_card(update, context)

    elif data.startswith("val_edit_"):
        context.user_data["awaiting_edit"] = True
        lang_name = LANGUAGES.get(item["lang"], {}).get("name", item["lang"])
        await query.answer("Awaiting your edit...")
        await query.edit_message_text(
            f"✏️ *Suggest a Correction for {lang_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🇬🇧 *English*:\n`{item['english']}`\n\n"
            f"Current draft:\n`{item['target']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 *Please type and send the correct translation as a reply message:*\n"
            f"_(Or type /cancel to go back)_",
            parse_mode="Markdown",
        )

    elif data == "menu_translate":
        context.user_data["awaiting_translation"] = True
        await query.answer()
        await query.edit_message_text(
            "🌐 *LISAN Translation Engine*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            "Send any word or sentence in Amharic, Oromo, Tigrinya, Somali, or English.\n\n"
            "The bot will match it across our 373,000+ bilingual phrase pairs!\n\n"
            "_(Type your sentence below)_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_home")]]),
        )


# ==========================================
# TEXT MESSAGE HANDLER (Edits & Translation)
# ==========================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text input for user corrections or dictionary searches."""
    user = update.effective_user
    text = update.message.text.strip()

    if text.lower() == "/cancel":
        context.user_data["awaiting_edit"] = False
        context.user_data["awaiting_translation"] = False
        await start_command(update, context)
        return

    # Check if user is submitting an edit
    if context.user_data.get("awaiting_edit"):
        item = context.user_data.get("current_item")
        if item:
            reviewer_id = f"tg_{user.id}"
            username = user.username or user.first_name

            # Save human edit to Supabase
            record_validation(
                tuple_id=item["tuple_id"],
                domain=item["domain"],
                english_text=item["english"],
                target_lang=item["lang"],
                original_target=item["target"],
                validated_text=text,
                status="edited",
                reviewer_id=reviewer_id,
                notes=f"Community edit submitted by @{username} ({user.id})",
            )
            profile = update_user_score(user.id, username, "edited")
            context.user_data["awaiting_edit"] = False

            await update.message.reply_text(
                f"🎉 *Thank you! Your correction has been recorded for the AI training set!*\n"
                f"🌟 *+30 XP earned!* (Total: `{profile['points']} XP` — {profile['rank']})\n\n"
                f"Here is your next sentence:",
                parse_mode="Markdown",
            )
            await send_new_validation_card(update, context)
            return

    # Direct translation / phrasebook lookup
    matched = search_phrasebook(text)
    if matched:
        reply = (
            f"📖 *LISAN Corpus Match Found*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🇬🇧 *English*: `{matched.get('english', 'N/A')}`\n"
            f"🇪🇹 *Amharic*: {matched.get('amh', 'N/A')}\n"
            f"🌳 *Afaan Oromoo*: {matched.get('orm', 'N/A')}\n"
            f"🇪🇷 *Tigrinya*: {matched.get('tir', 'N/A')}\n"
            f"🇸🇴 *Somali*: {matched.get('som', 'N/A')}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ Domain: {matched.get('domain', 'general')}"
        )
    else:
        reply = (
            f"🔍 *Search Result*:\n"
            f"No exact match found in the gold offline tuple bank for: `\"{text}\"`.\n\n"
            f"💡 _Would you like to validate community sentences instead?_"
        )

    keyboard = [
        [InlineKeyboardButton("🎯 Validate Sentences", callback_data="val_start")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_home")],
    ]
    await update.message.reply_text(
        reply, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def search_phrasebook(query: str) -> dict:
    """Searches memory tuples for exact or substring matches."""
    q = query.lower()
    if not CACHED_TUPLES:
        load_tuples()
    for t in CACHED_TUPLES:
        if q == t.get("english", "").lower():
            return t
        for lang in ("amh", "orm", "tir", "som"):
            if q == t.get(lang, "").lower():
                return t
    # Substring search
    if len(q) > 3:
        for t in CACHED_TUPLES:
            if q in t.get("english", "").lower():
                return t
    return {}


# ==========================================
# MAIN APP INITIALIZER
# ==========================================

def main():
    """Runs the Telegram bot."""
    token = TELEGRAM_BOT_TOKEN
    if not token:
        print("\n" + "=" * 70)
        print("⚠️  TELEGRAM_BOT_TOKEN is not set!")
        print("=" * 70)
        print("1. Open Telegram and message @BotFather")
        print("2. Type /newbot and follow instructions to get your Token")
        print("3. Run the bot with:")
        print("   $env:TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN'; python telegram_bot/bot.py")
        print("   OR add it to telegram_bot/.env")
        print("=" * 70 + "\n")
        return

    # Preload dataset
    load_tuples()

    app = ApplicationBuilder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("validate", validate_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🚀 LISAN Telegram Bot is live and listening for messages...")
    app.run_polling()


if __name__ == "__main__":
    main()
