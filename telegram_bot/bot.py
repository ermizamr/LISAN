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
import html
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
    """Formats a clean, resilient HTML card for Telegram."""
    lang_info = LANGUAGES.get(item["lang"], {"name": item["lang"], "flag": "🌐"})
    domain_label = DOMAIN_ICONS.get(item["domain"], item.get("domain", "general"))

    english_esc = html.escape(str(item.get("english", "")))
    target_esc = html.escape(str(item.get("target", "")))
    domain_esc = html.escape(str(domain_label))
    lang_name = html.escape(str(lang_info.get("name", "")))
    lang_native = html.escape(str(lang_info.get("native", "")))
    flag = lang_info.get("flag", "🌐")

    return (
        f"✨ <b>LISAN Community Validation Card</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>Domain</b>: {domain_esc}\n"
        f"{flag} <b>Language</b>: {lang_name} ({lang_native})\n\n"
        f"🇬🇧 <b>English</b>:\n"
        f"<code>{english_esc}</code>\n\n"
        f"{flag} <b>Translation</b>:\n"
        f"<b>{target_esc}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Is this translation accurate, authentic, and natural?</i>"
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
    first_name_esc = html.escape(user.first_name if user else "Friend")
    welcome_text = (
        f"👋 <b>Selam, {first_name_esc}!</b>\n\n"
        f"🌟 Welcome to <b>LISAN AI</b> (ልሳን) — the open-source multilingual AI engine for "
        f"Horn of Africa languages:\n"
        f"• 🇪🇹 <b>Amharic</b> (አማርኛ)\n"
        f"• 🌳 <b>Afaan Oromoo</b>\n"
        f"• 🇪🇷 <b>Tigrinya</b> (ትግርኛ)\n"
        f"• 🇸🇴 <b>Somali</b> (Soomaali)\n"
        f"• 🇬🇧 <b>English</b>\n\n"
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
        try:
            await update.callback_query.edit_message_text(
                welcome_text, parse_mode="HTML", reply_markup=reply_markup
            )
        except Exception:
            await update.callback_query.message.reply_text(
                welcome_text, parse_mode="HTML", reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            welcome_text, parse_mode="HTML", reply_markup=reply_markup
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
            await update.callback_query.answer()
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
                text, parse_mode="HTML", reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"edit_message_text failed ({e}), sending new message")
            await update.callback_query.message.reply_text(
                text, parse_mode="HTML", reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=reply_markup
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows global dataset and live Supabase validation statistics."""
    stats = get_global_stats()
    text = (
        f"📊 <b>LISAN Global Corpus & Validation Scorecard</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Total Bitext Dataset</b>: <code>373,276 pairs</code>\n"
        f"🔀 <b>Language Directions</b>: <code>20 pairs (All 5x4 symmetrical)</code>\n"
        f"💎 <b>Gold Multi-Way Tuples</b>: <code>3,421 concepts (17,105 sentences)</code>\n\n"
        f"🌐 <b>Live Community Consensus (Supabase)</b>:\n"
        f"• Total Submissions: <code>{stats['total']:,}</code>\n"
        f"• Approved by Community: <code>{stats['approved']:,}</code>\n"
        f"• Human Corrections (Edits): <code>{stats['edited']:,}</code>\n"
        f"• Quarantined / Rejected: <code>{stats['rejected']:,}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f'🔗 <b>Live Hub</b>: <a href="https://lisan.ermizamr.tech/validate.html">lisan.ermizamr.tech</a>'
    )

    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_home")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True
        )


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays top community contributors and personal score."""
    leaders = get_leaderboard(limit=5)
    uid = str(update.effective_user.id)
    all_stats = load_user_gamification()
    my_stats = all_stats.get(uid, {"points": 0, "rank": "🌱 Apprentice Linguist", "total_reviews": 0})

    text = (
        f"🏆 <b>LISAN Community Leaderboard</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )

    if leaders:
        for i, u in enumerate(leaders, 1):
            badge = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            username_esc = html.escape(str(u['username']))
            rank_esc = html.escape(str(u['rank']))
            text += f"{badge} <b>{username_esc}</b> — <code>{u['points']} XP</code> ({rank_esc})\n"
    else:
        text += "<i>No community reviews submitted yet. Be the first!</i>\n"

    my_rank_esc = html.escape(str(my_stats['rank']))
    text += (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Your Profile</b>:\n"
        f"• Rank: <b>{my_rank_esc}</b>\n"
        f"• Total Points: <code>{my_stats['points']} XP</code>\n"
        f"• Reviews Cast: <code>{my_stats['total_reviews']}</code>\n\n"
        f"💡 <i>Tip: Validating gives +10 XP, submitting a corrected translation gives +30 XP!</i>"
    )

    keyboard = [
        [InlineKeyboardButton("🎯 Earn XP Now", callback_data="val_start")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_home")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=reply_markup
        )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays open-source project info and links."""
    text = (
        f"ℹ️ <b>About LISAN (ልሳን) AI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"LISAN is an open-source initiative dedicated to advancing AI for low-resource "
        f"languages of the Horn of Africa.\n\n"
        f"• 📜 <b>License</b>: Apache 2.0 (Code) / CC-BY 4.0 (Corpus)\n"
        f'• 🐙 <b>GitHub</b>: <a href="https://github.com/ermizamr/LISAN">github.com/ermizamr/LISAN</a>\n'
        f'• 🌐 <b>Web Validation Hub</b>: <a href="https://lisan.ermizamr.tech/validate.html">lisan.ermizamr.tech</a>\n'
        f"• 🗄️ <b>Database</b>: Real-time Supabase PostgreSQL\n"
        f"• 🤖 <b>Target Models</b>: NLLB-200 600M / 1.3B, LLaMA-3 LoRA\n"
    )

    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_home")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True
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
        await query.answer()
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
            "🌍 <b>Select which language you want to review:</b>",
            parse_mode="HTML",
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
        await query.answer("Loading new sentence...")
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
        english_esc = html.escape(str(item["english"]))
        target_esc = html.escape(str(item["target"]))
        await query.answer("Awaiting your edit...")
        await query.edit_message_text(
            f"✏️ <b>Suggest a Correction for {html.escape(lang_name)}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🇬🇧 <b>English</b>:\n<code>{english_esc}</code>\n\n"
            f"Current draft:\n<code>{target_esc}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 <b>Please type and send the correct translation as a reply message:</b>\n"
            f"<i>(Or type /cancel to go back)</i>",
            parse_mode="HTML",
        )

    elif data == "menu_translate":
        context.user_data["awaiting_translation"] = True
        await query.answer()
        await query.edit_message_text(
            "🌐 <b>LISAN Translation Engine</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            "Send any word or sentence in Amharic, Oromo, Tigrinya, Somali, or English.\n\n"
            "The bot will match it across our 373,000+ bilingual phrase pairs!\n\n"
            "<i>(Type your sentence below)</i>",
            parse_mode="HTML",
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
                f"🎉 <b>Thank you! Your correction has been recorded for the AI training set!</b>\n"
                f"🌟 <b>+30 XP earned!</b> (Total: <code>{profile['points']} XP</code> — {html.escape(profile['rank'])})\n\n"
                f"Here is your next sentence:",
                parse_mode="HTML",
            )
            await send_new_validation_card(update, context)
            return

    # Direct translation / phrasebook lookup
    matched = search_phrasebook(text)
    if matched:
        reply = (
            f"📖 <b>LISAN Corpus Match Found</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🇬🇧 <b>English</b>: <code>{html.escape(matched.get('english', 'N/A'))}</code>\n"
            f"🇪🇹 <b>Amharic</b>: {html.escape(matched.get('amh', 'N/A'))}\n"
            f"🌳 <b>Afaan Oromoo</b>: {html.escape(matched.get('orm', 'N/A'))}\n"
            f"🇪🇷 <b>Tigrinya</b>: {html.escape(matched.get('tir', 'N/A'))}\n"
            f"🇸🇴 <b>Somali</b>: {html.escape(matched.get('som', 'N/A'))}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ Domain: {html.escape(matched.get('domain', 'general'))}"
        )
    else:
        text_esc = html.escape(text)
        reply = (
            f"🔍 <b>Search Result</b>:\n"
            f"No exact match found in the gold offline tuple bank for: <code>\"{text_esc}\"</code>.\n\n"
            f"💡 <i>Would you like to validate community sentences instead?</i>"
        )

    keyboard = [
        [InlineKeyboardButton("🎯 Validate Sentences", callback_data="val_start")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_home")],
    ]
    await update.message.reply_text(
        reply, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
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
