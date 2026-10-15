# LISAN Telegram Community Bot (ልሳን)

A community crowdsourcing and translation bot for Telegram that empowers native speakers of **Amharic**, **Afaan Oromoo**, **Tigrinya**, **Somali**, and **English** to validate, edit, and curate datasets for open-source AI training.

---

## Key Features

1. 🎯 **Micro-Task Sentence Validation:** Native speakers review translations one by one using interactive inline buttons (`👍 Good`, `👎 Bad`, `✏️ Suggest Edit`, `⏭️ Skip`).
2. 🔄 **Direct Supabase Sync:** Every vote and text edit is stored immediately in the centralized Supabase database (`community_validations`), matching web portal submissions.
3. 🏆 **Gamified Contributor Tiers:** Reviewers earn Experience Points (XP), climb ranks (Apprentice $\rightarrow$ Mastermind), and compete on community leaderboards.
4. 🌐 **Multi-Way Translation & Corpus Lookup:** Instant dictionary and phrase search across the 3,421 multi-way gold concepts.
5. 📊 **Live Stats Dashboard:** Displays corpus size (373,276 pairs) and live community consensus counts.

---

## 🚀 How to Run the Bot

### Step 1: Get a Telegram Bot Token (30 seconds)
1. Open the Telegram app and search for `@BotFather`.
2. Send `/start`, then send `/newbot`.
3. Choose a name (e.g., `LISAN AI Assistant`) and a username (e.g., `LisanAIBot` or `LisanTranslatorBot`).
4. `@BotFather` will reply with your **API Token** (looks like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

### Step 2: Set the Token & Run
In PowerShell:
```powershell
# Set your token
$env:TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"

# Run the bot
python telegram_bot/bot.py
```

Or copy `telegram_bot/.env.example` to `telegram_bot/.env` and insert your token.

---

## 📱 Bot Commands for Users

| Command | Action |
| :--- | :--- |
| `/start` | Opens the main menu with interactive navigation buttons. |
| `/validate` | Starts the sentence validation micro-task flow. |
| `/stats` | Shows global dataset numbers and live Supabase review tallies. |
| `/leaderboard` | Displays top contributors by XP and personal ranking. |
| `/about` | Displays open-source licenses, GitHub links, and model details. |
| `/cancel` | Exits edit mode and returns to the main menu. |

---

## 🔗 Architecture

```
Telegram User ──> [Telegram Bot API] ──> [telegram_bot/bot.py]
                                                 │
                                                 ├──> [Supabase Cloud DB (community_validations)]
                                                 │          │
                                                 │          ▼
                                                 │    scripts/sync_community_to_dataset.py
                                                 │          │
                                                 │          ▼
                                                 └──> LoRA AI Training Set (community_verified.jsonl)
```
