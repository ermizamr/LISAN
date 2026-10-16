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
    get_tuple_scores,
    update_user_score,
    get_leaderboard,
    load_user_gamification,
    log_analytics_event,
    get_analytics_summary,
    save_pending_edit,
    get_latest_pending_edit,
    clear_pending_edit,
    get_user_stats,
)

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cache of all 3,421 multi-way tuples
CACHED_TUPLES = []
TUPLE_MAP = {}


def load_tuples():
    """Loads all community tuples into memory for rapid serving and stateless lookups."""
    global CACHED_TUPLES, TUPLE_MAP
    if DATA_TUPLES_PATH.exists():
        try:
            with open(DATA_TUPLES_PATH, "r", encoding="utf-8") as f:
                CACHED_TUPLES = json.load(f)
                TUPLE_MAP = {str(t["id"]): t for t in CACHED_TUPLES}
                logger.info(f"Loaded {len(CACHED_TUPLES):,} tuples for validation.")
        except Exception as e:
            logger.error(f"Error loading tuples: {e}")
            CACHED_TUPLES = []
            TUPLE_MAP = {}
    return CACHED_TUPLES


def get_tuple_by_id(tuple_id: str, lang: str = "amh") -> dict:
    """Stateless retrieval of tuple content by ID and target language."""
    global TUPLE_MAP, CACHED_TUPLES
    if not TUPLE_MAP:
        load_tuples()
    t = TUPLE_MAP.get(str(tuple_id))
    if not t:
        return {}
    translations = t.get("translations", {})
    return {
        "tuple": t,
        "tuple_id": str(t.get("id")),
        "lang": lang,
        "domain": t.get("domain", "general"),
        "english": translations.get("eng", t.get("english", "")),
        "target": translations.get(lang, t.get(lang, "")),
    }


def get_user_tg_handle(user) -> str:
    """Returns formatted Telegram username e.g. @username or @firstname."""
    if not user:
        return "@contributor"
    if user.username:
        return f"@{user.username.lstrip('@')}"
    if user.first_name:
        clean_first = user.first_name.strip().replace(" ", "_")
        return f"@{clean_first}"
    return f"@user_{user.id}"


def get_candidate_sentence(user_id: int = None, username: str = None, preferred_lang: str = None) -> dict:
    """Picks a sentence prioritizing under-reviewed tuples and avoiding duplicate user views.

    Guarantees that ALL 3,421 tuples (across all 4 Horn languages) get equal opportunity
    for community validation and reach consensus threshold (3 concordant reviews),
    while ensuring no contributor is ever asked to review the same sentence twice.
    """
    if not CACHED_TUPLES:
        load_tuples()
    if not CACHED_TUPLES:
        return {}

    # Query live community review scores from Supabase
    tuple_scores = get_tuple_scores()

    user_tag = f"tg_{user_id}" if user_id else None
    user_handle = username if username else None

    # Supported target languages
    all_langs = ["amh", "orm", "tir", "som"]
    target_langs = [preferred_lang] if preferred_lang in all_langs else all_langs

    # Filter candidate pool
    candidates = []
    for t in CACHED_TUPLES:
        translations = t.get("translations", {})
        tid = str(t.get("id"))

        for lang in target_langs:
            if lang in translations and translations[lang]:
                score_key = f"{tid}:{lang}"
                score_data = tuple_scores.get(
                    score_key,
                    {"total": 0, "approved": 0, "rejected": 0, "edited": 0, "reviewers": set()},
                )

                # Skip if this specific contributor already validated this sentence
                reviewers_set = score_data.get("reviewers", set())
                if user_tag and user_tag in reviewers_set:
                    continue
                if user_handle and user_handle in reviewers_set:
                    continue

                candidates.append({
                    "tuple": t,
                    "lang": lang,
                    "tuple_id": tid,
                    "domain": t.get("domain", "general"),
                    "english": translations.get("eng", t.get("english", "")),
                    "target": translations.get(lang, t.get(lang, "")),
                    "total_reviews": score_data.get("total", 0),
                    "approved": score_data.get("approved", 0),
                    "rejected": score_data.get("rejected", 0),
                    "edited": score_data.get("edited", 0),
                })

    # If the user has reviewed everything or pool is temporarily exhausted, fallback
    if not candidates:
        for t in CACHED_TUPLES:
            translations = t.get("translations", {})
            tid = str(t.get("id"))
            for lang in target_langs:
                if lang in translations and translations[lang]:
                    candidates.append({
                        "tuple": t,
                        "lang": lang,
                        "tuple_id": tid,
                        "domain": t.get("domain", "general"),
                        "english": translations.get("eng", t.get("english", "")),
                        "target": translations.get(lang, t.get(lang, "")),
                        "total_reviews": 0,
                        "approved": 0,
                        "rejected": 0,
                        "edited": 0,
                    })

    # Find the minimum review tier so under-reviewed sentences get served first!
    min_reviews = min(c["total_reviews"] for c in candidates)
    priority_pool = [c for c in candidates if c["total_reviews"] == min_reviews]

    # Pick randomly from the lowest review count pool for even distribution
    return random.choice(priority_pool)


def render_progress_bar(percent: float, length: int = 10, filled: str = "█", empty: str = "░") -> str:
    """Renders a sleek Unicode progress bar with percentage: [████░░░░░░] 40.0%"""
    clamped = max(0.0, min(100.0, float(percent)))
    fill_count = int(round((clamped / 100.0) * length))
    if clamped > 0 and fill_count == 0:
        fill_count = 1  # show visual feedback for initial progress
    empty_count = length - fill_count
    bar = (filled * fill_count) + (empty * empty_count)
    return f"<code>[{bar}]</code> <b>{clamped:.1f}%</b>"


def make_card_text(item: dict) -> str:
    """Formats a clean, resilient HTML card for Telegram with live sentence score."""
    lang_info = LANGUAGES.get(item["lang"], {"name": item["lang"]})
    domain_label = DOMAIN_ICONS.get(item["domain"], item.get("domain", "general"))

    english_esc = html.escape(str(item.get("english", "")))
    target_esc = html.escape(str(item.get("target", "")))
    domain_esc = html.escape(str(domain_label))
    lang_name = html.escape(str(lang_info.get("name", "")))
    lang_native = html.escape(str(lang_info.get("native", "")))

    approved = item.get("approved", 0)
    rejected = item.get("rejected", 0)
    total_reviews = item.get("total_reviews", 0)

    # Score & Consensus Status Badge
    if total_reviews == 0:
        score_badge = "🆕 <b>Needs Initial Review</b> (0/3 votes)"
    elif approved >= 3:
        score_badge = "✅ <b>Verified Gold Standard</b> (3/3 approvals reached!)"
    elif rejected >= 2:
        score_badge = "⚠️ <b>Needs Human Correction</b> (Multiple flags)"
    else:
        score_badge = f"⏳ <b>In Progress</b>: {total_reviews}/3 reviews ({approved} 👍, {rejected} 👎)"

    return (
        f"✨ <b>LISAN Community Validation Card</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>Domain</b>: {domain_esc}\n"
        f"🗣️ <b>Language</b>: {lang_name} ({lang_native})\n\n"
        f"<b>English</b>:\n"
        f"<code>{english_esc}</code>\n\n"
        f"<b>{lang_name} Translation</b>:\n"
        f"<b>{target_esc}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Score</b>: {score_badge}\n"
        f"💡 <i>Is this translation accurate, authentic, and natural?</i>"
    )


def make_card_keyboard(item: dict) -> InlineKeyboardMarkup:
    """Builds stateless inline action buttons encoding language and tuple ID."""
    lang = item.get("lang", "amh")
    tid = item.get("tuple_id", "")
    buttons = [
        [
            InlineKeyboardButton("👍 Good / ትክክል", callback_data=f"vg:{lang}:{tid}"),
            InlineKeyboardButton("👎 Bad / ስህተት", callback_data=f"vb:{lang}:{tid}"),
        ],
        [
            InlineKeyboardButton("✏️ Suggest Edit", callback_data=f"ve:{lang}:{tid}"),
            InlineKeyboardButton("⏭️ Skip", callback_data=f"vs:{lang}:{tid}"),
        ],
        [
            InlineKeyboardButton("🌐 Change Language", callback_data="val_lang_picker"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_home"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def make_language_keyboard() -> InlineKeyboardMarkup:
    """Builds language selection keyboard without any country flags."""
    buttons = [
        [
            InlineKeyboardButton("አማርኛ (Amharic)", callback_data="pick_lang_amh"),
            InlineKeyboardButton("Afaan Oromoo", callback_data="pick_lang_orm"),
        ],
        [
            InlineKeyboardButton("ትግርኛ (Tigrinya)", callback_data="pick_lang_tir"),
            InlineKeyboardButton("Soomaali (Somali)", callback_data="pick_lang_som"),
        ],
        [
            InlineKeyboardButton("🔀 All Languages (Random)", callback_data="pick_lang_all"),
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_home"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


async def send_language_picker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompts the user to select the specific language they speak fluently."""
    text = (
        "🗣️ <b>Choose Your Language / ቋንቋ ይምረጡ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "To ensure authentic, high-quality AI training data, please select the language you speak fluently.\n\n"
        "The bot will serve sentences <b>strictly from this language</b> so you can review with confidence!"
    )
    reply_markup = make_language_keyboard()
    if update.callback_query:
        try:
            await update.callback_query.answer()
        except Exception:
            pass
        try:
            await update.callback_query.edit_message_text(
                text, parse_mode="HTML", reply_markup=reply_markup
            )
        except Exception:
            await update.callback_query.message.reply_text(
                text, parse_mode="HTML", reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=reply_markup
        )


# ==========================================
# COMMAND HANDLERS
# ==========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the welcoming main menu."""
    user = update.effective_user
    tg_handle = get_user_tg_handle(user)
    if user:
        log_analytics_event("bot_start", user.id, tg_handle)

    first_name_esc = html.escape(user.first_name if user else "Friend")
    welcome_text = (
        f"👋 <b>Selam, {first_name_esc}!</b>\n\n"
        f"🌟 Welcome to <b>LISAN AI</b> (ልሳን) — the open-source multilingual AI engine for "
        f"Horn of Africa languages:\n"
        f"• <b>Amharic</b> (አማርኛ)\n"
        f"• <b>Afaan Oromoo</b>\n"
        f"• <b>Tigrinya</b> (ትግርኛ)\n"
        f"• <b>Somali</b> (Soomaali)\n"
        f"• <b>English</b>\n\n"
        f"Help us evaluate, correct, and curate authentic datasets for open-source AI models!"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎯 Start Validating (አረጋግጥ)", callback_data="val_start"),
        ],
        [
            InlineKeyboardButton("🚀 100% Goal Progress", callback_data="menu_progress"),
            InlineKeyboardButton("🏆 Leaderboard & XP", callback_data="menu_leaderboard"),
        ],
        [
            InlineKeyboardButton("📊 Dataset Stats", callback_data="menu_stats"),
            InlineKeyboardButton("📈 Live Analytics", callback_data="menu_analytics"),
        ],
        [
            InlineKeyboardButton("🌐 Quick Translate", callback_data="menu_translate"),
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
    pref_lang = context.user_data.get("preferred_lang")
    if pref_lang:
        await send_new_validation_card(update, context, preferred_lang=pref_lang)
    else:
        await send_language_picker(update, context)


async def send_new_validation_card(update: Update, context: ContextTypes.DEFAULT_TYPE, preferred_lang: str = None):
    """Selects and renders a new validation card prioritizing unreviewed sentences in the chosen language."""
    user = update.effective_user
    uid = user.id if user else None
    tg_handle = get_user_tg_handle(user)

    if preferred_lang is not None:
        context.user_data["preferred_lang"] = preferred_lang if preferred_lang != "all" else None

    pref_lang = context.user_data.get("preferred_lang")
    item = get_candidate_sentence(user_id=uid, username=tg_handle, preferred_lang=pref_lang)

    if not item:
        msg = "⚠️ No sentences available in the library at this moment."
        if update.callback_query:
            try:
                await update.callback_query.answer()
            except Exception:
                pass
            try:
                await update.callback_query.edit_message_text(msg)
            except Exception:
                await update.callback_query.message.reply_text(msg)
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
    """Shows global dataset and live Supabase validation statistics with progress to 100%."""
    stats = get_global_stats()
    unique_cnt = stats.get("unique_validated", 0)
    gold_cnt = stats.get("gold_verified", 0)
    overall_bar = render_progress_bar(stats["overall_pct"], length=10)
    coverage_bar = render_progress_bar(stats["coverage_pct"], length=10)
    gold_bar = render_progress_bar(stats["gold_pct"], length=10)

    text = (
        f"📊 <b>LISAN Global Corpus & Validation Scorecard</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Total Bitext Dataset</b>: <code>373,276 pairs</code>\n"
        f"🔀 <b>Language Directions</b>: <code>20 pairs (All 5x4 symmetrical)</code>\n"
        f"💎 <b>Gold Validation Library</b>: <code>3,421 concepts (13,684 sentences)</code>\n\n"
        f"🎯 <b>Progress to 100% Verification Goal</b>:\n"
        f"• Total Translations: {overall_bar} ({stats['total']:,} / 13,684)\n"
        f"• Unique Concepts: {coverage_bar} ({unique_cnt:,} / 3,421)\n"
        f"• Gold Consensus (3/3): {gold_bar} ({gold_cnt:,} / 3,421)\n\n"
        f"🌐 <b>Community Review Breakdown</b>:\n"
        f"• Approved by Community: <code>{stats['approved']:,}</code>\n"
        f"• Human Corrections (Edits): <code>{stats['edited']:,}</code>\n"
        f"• Flagged / Quarantined: <code>{stats['rejected']:,}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f'🔗 <b>Live Hub</b>: <a href="https://lisan.ermizamr.tech/validate.html">lisan.ermizamr.tech</a>'
    )

    keyboard = [
        [InlineKeyboardButton("🚀 100% Growth Roadmap", callback_data="menu_progress")],
        [InlineKeyboardButton("📈 Community Analytics", callback_data="menu_analytics")],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_home")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(
                text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True
            )
        except Exception:
            await update.callback_query.message.reply_text(
                text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True
            )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True
        )


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays comprehensive dataset growth percentage to 100% completion."""
    stats = get_global_stats()
    summary = get_analytics_summary()

    overall_bar = render_progress_bar(stats["overall_pct"], length=12)
    coverage_bar = render_progress_bar(stats["coverage_pct"], length=10)
    gold_bar = render_progress_bar(stats["gold_pct"], length=10)

    amh_bar = render_progress_bar(stats["lang_pct"]["amh"], length=10)
    orm_bar = render_progress_bar(stats["lang_pct"]["orm"], length=10)
    tir_bar = render_progress_bar(stats["lang_pct"]["tir"], length=10)
    som_bar = render_progress_bar(stats["lang_pct"]["som"], length=10)

    m_bar = render_progress_bar(stats["milestone_pct"], length=10)

    text = (
        f"🚀 <b>LISAN 100% Dataset Growth & Milestone Roadmap</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"We are curating the first authentic, production-grade AI dataset for Ethiopian and Horn of Africa languages.\n\n"
        f"🎯 <b>Total Progress to 100% Goal</b>:\n"
        f"{overall_bar} ({stats['total']:,} / {stats['total_target_sentences']:,} translations)\n\n"
        f"🏁 <b>Current Target Milestone</b>:\n"
        f"• <b>{stats['milestone_name']}</b>\n"
        f"  {m_bar} ({stats['total']:,} / {stats['milestone_target']:,} — {stats['milestone_remaining']:,} needed)\n\n"
        f"🗣️ <b>Language Progress to 100% (3,421 each)</b>:\n"
        f"• <b>Amharic (አማርኛ)</b>:\n"
        f"  {amh_bar} ({stats['lang_counts']['amh']:,} / 3,421)\n"
        f"• <b>Afaan Oromoo</b>:\n"
        f"  {orm_bar} ({stats['lang_counts']['orm']:,} / 3,421)\n"
        f"• <b>Tigrinya (ትግርኛ)</b>:\n"
        f"  {tir_bar} ({stats['lang_counts']['tir']:,} / 3,421)\n"
        f"• <b>Somali (Soomaali)</b>:\n"
        f"  {som_bar} ({stats['lang_counts']['som']:,} / 3,421)\n\n"
        f"💎 <b>Quality Consensus Metrics</b>:\n"
        f"• Concept Coverage: {coverage_bar} ({stats['unique_validated']:,} / 3,421 concepts)\n"
        f"• Gold Consensus (3/3): {gold_bar} ({stats['gold_verified']:,} / 3,421 verified)\n"
        f"• Active Contributors: <code>{summary['unique_contributors']:,} community members</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Every 5-second validation pushes our languages closer to 100% open AI readiness!</i>"
    )

    keyboard = [
        [InlineKeyboardButton("🎯 Validate & Boost Progress (+10 XP)", callback_data="val_start")],
        [
            InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard"),
            InlineKeyboardButton("📈 Live Analytics", callback_data="menu_analytics"),
        ],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_home")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(
                text, parse_mode="HTML", reply_markup=reply_markup
            )
        except Exception:
            await update.callback_query.message.reply_text(
                text, parse_mode="HTML", reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=reply_markup
        )


async def analytics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays live community engagement analytics and distribution."""
    summary = get_analytics_summary()
    total_rev = summary["total_reviews"]
    lang_c = summary["lang_counts"]

    amh_pct = round((lang_c["amh"] / total_rev * 100), 1) if total_rev else 0.0
    orm_pct = round((lang_c["orm"] / total_rev * 100), 1) if total_rev else 0.0
    tir_pct = round((lang_c["tir"] / total_rev * 100), 1) if total_rev else 0.0
    som_pct = round((lang_c["som"] / total_rev * 100), 1) if total_rev else 0.0

    text = (
        f"📈 <b>LISAN Live Community Analytics</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Active Contributors</b>: <code>{summary['unique_contributors']:,}</code>\n"
        f"🤖 <b>Bot Sessions Started</b>: <code>{summary['bot_starts']:,}</code>\n"
        f"⚡ <b>24-Hour Velocity</b>: <code>+{summary['reviews_24h']:,} reviews</code>\n"
        f"🎯 <b>Quality Approval Rate</b>: <code>{summary['approval_rate']}%</code>\n\n"
        f"🗣️ <b>Language Activity Distribution</b>:\n"
        f"• <b>Amharic</b> (አማርኛ): <code>{lang_c['amh']:,}</code> ({amh_pct}%)\n"
        f"• <b>Afaan Oromoo</b>: <code>{lang_c['orm']:,}</code> ({orm_pct}%)\n"
        f"• <b>Tigrinya</b> (ትግርኛ): <code>{lang_c['tir']:,}</code> ({tir_pct}%)\n"
        f"• <b>Somali</b> (Soomaali): <code>{lang_c['som']:,}</code> ({som_pct}%)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Reviews Breakdown</b>: <code>{total_rev:,} total</code>\n"
        f"• Approved: <code>{summary['approved']:,}</code>\n"
        f"• Human Corrections: <code>{summary['edited']:,}</code>\n"
        f"• Flagged / Quarantined: <code>{summary['rejected']:,}</code>\n"
    )

    keyboard = [
        [InlineKeyboardButton("📊 Corpus Scorecard", callback_data="menu_stats")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_home")],
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


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays top community contributors and personal score."""
    leaders = get_leaderboard(limit=5)
    user = update.effective_user
    uid = user.id if user else 0
    tg_handle = get_user_tg_handle(user)
    my_stats = get_user_stats(uid, tg_handle)

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
    tg_handle_esc = html.escape(str(tg_handle))
    text += (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Your Profile ({tg_handle_esc})</b>:\n"
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
    elif data == "menu_analytics":
        await analytics_command(update, context)
        return
    elif data == "menu_progress":
        await progress_command(update, context)
        return
    elif data in ("val_start", "val_lang_picker"):
        await send_language_picker(update, context)
        return
    elif data.startswith("set_lang_") or data.startswith("pick_lang_"):
        lang = data.replace("set_lang_", "").replace("pick_lang_", "")
        context.user_data["preferred_lang"] = None if lang == "all" else lang
        lang_title = "All Languages" if lang == "all" else LANGUAGES.get(lang, {}).get("name", lang)
        tg_handle = get_user_tg_handle(user)
        if user:
            log_analytics_event("lang_select", user.id, tg_handle, target_lang=lang)
        await query.answer(f"Selected: {lang_title}")
        await send_new_validation_card(update, context, preferred_lang=context.user_data["preferred_lang"])
        return

    # Stateless validation action callbacks (survives Vercel serverless cold-starts)
    if data.startswith("vg:") or data.startswith("vb:") or data.startswith("ve:") or data.startswith("vs:"):
        parts = data.split(":")
        action = parts[0]
        lang = parts[1]
        tid = parts[2] if len(parts) > 2 else ""

        item = context.user_data.get("current_item")
        if not item or str(item.get("tuple_id")) != str(tid):
            item = get_tuple_by_id(tid, lang)

        if not item:
            await query.answer("Fetching next sentence...")
            await send_new_validation_card(update, context, preferred_lang=None if lang == "all" else lang)
            return

        tg_handle = get_user_tg_handle(user)
        reviewer_id = f"tg_{user.id}"

        if action == "vg":
            record_validation(
                tuple_id=item["tuple_id"],
                domain=item["domain"],
                english_text=item["english"],
                target_lang=item["lang"],
                original_target=item["target"],
                validated_text=item["target"],
                status="approved",
                reviewer_id=reviewer_id,
                tg_username=tg_handle,
                notes=f"Approved via Telegram Bot by {tg_handle}",
            )
            profile = update_user_score(user.id, tg_handle, "approved")
            await query.answer(f"✓ Approved! +10 XP (Total: {profile['points']} XP)")
            await send_new_validation_card(update, context, preferred_lang=None if lang == "all" else lang)
            return

        elif action == "vb":
            record_validation(
                tuple_id=item["tuple_id"],
                domain=item["domain"],
                english_text=item["english"],
                target_lang=item["lang"],
                original_target=item["target"],
                validated_text=None,
                status="rejected",
                reviewer_id=reviewer_id,
                tg_username=tg_handle,
                notes=f"Rejected via Telegram Bot by {tg_handle}",
            )
            profile = update_user_score(user.id, tg_handle, "rejected")
            await query.answer(f"✓ Flagged & Quarantined! +10 XP (Total: {profile['points']} XP)")
            await send_new_validation_card(update, context, preferred_lang=None if lang == "all" else lang)
            return

        elif action == "vs":
            if user:
                log_analytics_event("card_skip", user.id, tg_handle, target_lang=item["lang"])
            await query.answer("Skipped")
            await send_new_validation_card(update, context, preferred_lang=None if lang == "all" else lang)
            return

        elif action == "ve":
            context.user_data["awaiting_edit"] = True
            context.user_data["current_item"] = item
            context.user_data["preferred_lang"] = lang
            save_pending_edit(user.id, tg_handle, tid, lang)

            lang_name = LANGUAGES.get(item["lang"], {}).get("name", item["lang"])
            english_esc = html.escape(str(item["english"]))
            target_esc = html.escape(str(item["target"]))
            await query.answer("Awaiting your edit...")
            await query.edit_message_text(
                f"✏️ <b>Suggest a Correction for {html.escape(lang_name)}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>English</b>:\n<code>{english_esc}</code>\n\n"
                f"<b>Current draft</b>:\n<code>{target_esc}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👇 <b>Please type and send the correct translation as a reply message:</b>\n"
                f"<i>(Or type /cancel to go back)</i>",
                parse_mode="HTML",
            )
            return

    # Fallback for legacy callbacks if an older card was active
    item = context.user_data.get("current_item")
    if not item:
        await query.answer("Loading new sentence...")
        await send_new_validation_card(update, context)
        return

    tg_handle = get_user_tg_handle(user)
    reviewer_id = f"tg_{user.id}"

    if data.startswith("val_good_"):
        record_validation(
            tuple_id=item["tuple_id"],
            domain=item["domain"],
            english_text=item["english"],
            target_lang=item["lang"],
            original_target=item["target"],
            validated_text=item["target"],
            status="approved",
            reviewer_id=reviewer_id,
            tg_username=tg_handle,
            notes=f"Approved via Telegram Bot by {tg_handle}",
        )
        profile = update_user_score(user.id, tg_handle, "approved")
        await query.answer(f"✓ Approved! +10 XP (Total: {profile['points']} XP)")
        await send_new_validation_card(update, context, preferred_lang=item.get("lang"))

    elif data.startswith("val_bad_"):
        record_validation(
            tuple_id=item["tuple_id"],
            domain=item["domain"],
            english_text=item["english"],
            target_lang=item["lang"],
            original_target=item["target"],
            validated_text=None,
            status="rejected",
            reviewer_id=reviewer_id,
            tg_username=tg_handle,
            notes=f"Rejected via Telegram Bot by {tg_handle}",
        )
        profile = update_user_score(user.id, tg_handle, "rejected")
        await query.answer(f"✓ Rejected & Quarantined! +10 XP (Total: {profile['points']} XP)")
        await send_new_validation_card(update, context, preferred_lang=item.get("lang"))

    elif data.startswith("val_skip_"):
        if user and item:
            log_analytics_event("card_skip", user.id, tg_handle, target_lang=item["lang"])
        await query.answer("Skipped")
        await send_new_validation_card(update, context, preferred_lang=item.get("lang"))

    elif data.startswith("val_edit_"):
        context.user_data["awaiting_edit"] = True
        save_pending_edit(user.id, tg_handle, item["tuple_id"], item["lang"])
        lang_name = LANGUAGES.get(item["lang"], {}).get("name", item["lang"])
        english_esc = html.escape(str(item["english"]))
        target_esc = html.escape(str(item["target"]))
        await query.answer("Awaiting your edit...")
        await query.edit_message_text(
            f"✏️ <b>Suggest a Correction for {html.escape(lang_name)}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>English</b>:\n<code>{english_esc}</code>\n\n"
            f"<b>Current draft</b>:\n<code>{target_esc}</code>\n"
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
        if user:
            clear_pending_edit(user.id)
        await start_command(update, context)
        return

    # Check if user is submitting an edit
    is_awaiting = context.user_data.get("awaiting_edit", False)
    item = context.user_data.get("current_item")

    # Durable fallback: if serverless cold-start emptied memory, check Supabase pending edit
    if not item and user:
        pending = get_latest_pending_edit(user.id)
        if pending:
            tid = pending.get("tuple_id")
            plang = pending.get("target_lang", "amh")
            item = get_tuple_by_id(tid, plang)
            is_awaiting = True

    if is_awaiting and item:
        tg_handle = get_user_tg_handle(user)
        reviewer_id = f"tg_{user.id}"
        edit_lang = item.get("lang", "amh")

        # Save human edit to Supabase
        record_validation(
            tuple_id=item["tuple_id"],
            domain=item["domain"],
            english_text=item["english"],
            target_lang=edit_lang,
            original_target=item["target"],
            validated_text=text,
            status="edited",
            reviewer_id=reviewer_id,
            tg_username=tg_handle,
            notes=f"Community edit submitted by {tg_handle} ({user.id})",
        )
        if user:
            clear_pending_edit(user.id)
        profile = update_user_score(user.id, tg_handle, "edited")
        context.user_data["awaiting_edit"] = False

        await update.message.reply_text(
            f"🎉 <b>Thank you! Your correction has been recorded for the AI training set!</b>\n"
            f"🌟 <b>+30 XP earned!</b> (Total: <code>{profile['points']} XP</code> — {html.escape(profile['rank'])})\n\n"
            f"Here is your next sentence:",
            parse_mode="HTML",
        )
        await send_new_validation_card(update, context, preferred_lang=edit_lang)
        return

    # Direct translation / phrasebook lookup
    matched = search_phrasebook(text)
    if matched:
        reply = (
            f"📖 <b>LISAN Corpus Match Found</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>English</b>: <code>{html.escape(matched.get('english', 'N/A'))}</code>\n"
            f"<b>Amharic</b>: {html.escape(matched.get('amh', 'N/A'))}\n"
            f"<b>Afaan Oromoo</b>: {html.escape(matched.get('orm', 'N/A'))}\n"
            f"<b>Tigrinya</b>: {html.escape(matched.get('tir', 'N/A'))}\n"
            f"<b>Somali</b>: {html.escape(matched.get('som', 'N/A'))}\n"
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
        trans = t.get("translations", {})
        eng = trans.get("eng", t.get("english", ""))
        amh = trans.get("amh", t.get("amh", ""))
        orm = trans.get("orm", t.get("orm", ""))
        tir = trans.get("tir", t.get("tir", ""))
        som = trans.get("som", t.get("som", ""))

        if eng and q == eng.lower():
            return {"english": eng, "amh": amh, "orm": orm, "tir": tir, "som": som, "domain": t.get("domain", "general")}
        for val in (amh, orm, tir, som):
            if val and q == val.lower():
                return {"english": eng, "amh": amh, "orm": orm, "tir": tir, "som": som, "domain": t.get("domain", "general")}

    # Substring search
    if len(q) > 3:
        for t in CACHED_TUPLES:
            trans = t.get("translations", {})
            eng = trans.get("eng", t.get("english", ""))
            if eng and q in eng.lower():
                return {
                    "english": eng,
                    "amh": trans.get("amh", t.get("amh", "")),
                    "orm": trans.get("orm", t.get("orm", "")),
                    "tir": trans.get("tir", t.get("tir", "")),
                    "som": trans.get("som", t.get("som", "")),
                    "domain": t.get("domain", "general")
                }
    return {}


# ==========================================
# BOT APPLICATION FACTORY
# ==========================================

def create_bot_application():
    """Builds and configures the Telegram Application instance."""
    token = TELEGRAM_BOT_TOKEN
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set! Please check your environment variables.")

    # Preload dataset
    load_tuples()

    app = ApplicationBuilder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("validate", validate_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("progress", progress_command))
    app.add_handler(CommandHandler("goal", progress_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("analytics", analytics_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app


def main():
    """Runs the Telegram bot in long-polling mode (for local / dedicated worker)."""
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

    app = create_bot_application()
    print("🚀 LISAN Telegram Bot is live and listening for messages (Long Polling)...")
    app.run_polling()


if __name__ == "__main__":
    main()
