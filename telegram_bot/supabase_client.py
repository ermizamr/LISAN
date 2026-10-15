"""Supabase client and gamified contributor stats for LISAN Telegram Bot."""

import json
import urllib.request
import urllib.error
from pathlib import Path
from telegram_bot.config import SUPABASE_URL, SUPABASE_KEY, LOCAL_USER_STATS_PATH

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def record_validation(
    tuple_id: str,
    domain: str,
    english_text: str,
    target_lang: str,
    original_target: str,
    validated_text: str,
    status: str,
    reviewer_id: str,
    notes: str = "",
) -> bool:
    """Inserts a community review record into Supabase PostgreSQL."""
    endpoint = f"{SUPABASE_URL}/rest/v1/community_validations"
    reviewer_str = f"tg:{reviewer_id}"
    full_note = f"{reviewer_str} | {notes}" if notes else reviewer_str

    payload = {
        "tuple_id": str(tuple_id),
        "domain": str(domain),
        "english_text": str(english_text),
        "target_lang": str(target_lang),
        "original_target": str(original_target),
        "validated_text": str(validated_text) if validated_text else None,
        "status": str(status),
        "reviewer_note": full_note,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data, headers=HEADERS, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 201)
    except Exception as e:
        print(f"[Supabase Error] Failed to write validation: {e}")
        return False


def get_tuple_scores() -> dict:
    """Fetches review scores and validation counts per (tuple_id, target_lang) from Supabase."""
    endpoint = f"{SUPABASE_URL}/rest/v1/community_validations?select=tuple_id,target_lang,status,reviewer_note"
    req = urllib.request.Request(
        endpoint,
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
    )
    scores = {}
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            rows = json.loads(response.read().decode("utf-8"))
            for r in rows:
                tid = str(r.get("tuple_id"))
                lang = str(r.get("target_lang"))
                status = str(r.get("status"))
                rev_note = str(r.get("reviewer_note") or "")

                key = f"{tid}:{lang}"
                if key not in scores:
                    scores[key] = {
                        "approved": 0,
                        "rejected": 0,
                        "edited": 0,
                        "total": 0,
                        "reviewers": set(),
                    }
                if status in ("approved", "edited"):
                    scores[key]["approved"] += 1
                elif status == "rejected":
                    scores[key]["rejected"] += 1
                if status == "edited":
                    scores[key]["edited"] += 1
                scores[key]["total"] += 1

                # Extract reviewer tag for deduplication
                if "tg:" in rev_note:
                    parts = rev_note.split("|")[0].replace("tg:", "").strip()
                    scores[key]["reviewers"].add(parts)
    except Exception as e:
        print(f"[Supabase Error] Failed to fetch tuple scores: {e}")
    return scores


def get_global_stats() -> dict:
    """Fetches total review counts, unique corpus coverage, and gold-verified count from Supabase."""
    endpoint = f"{SUPABASE_URL}/rest/v1/community_validations?select=tuple_id,target_lang,status"
    req = urllib.request.Request(
        endpoint,
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            rows = json.loads(response.read().decode("utf-8"))
            total = len(rows)
            approved = sum(1 for r in rows if r.get("status") in ("approved", "edited"))
            rejected = sum(1 for r in rows if r.get("status") == "rejected")
            edited = sum(1 for r in rows if r.get("status") == "edited")

            # Track unique tuple coverage and consensus
            tuple_approvals = {}
            for r in rows:
                tid = r.get("tuple_id")
                if tid and r.get("status") in ("approved", "edited"):
                    tuple_approvals[tid] = tuple_approvals.get(tid, 0) + 1

            unique_validated = len(tuple_approvals)
            gold_verified = sum(1 for cnt in tuple_approvals.values() if cnt >= 3)

            return {
                "total": total,
                "approved": approved,
                "rejected": rejected,
                "edited": edited,
                "unique_validated": unique_validated,
                "gold_verified": gold_verified,
            }
    except Exception as e:
        print(f"[Supabase Error] Failed to get stats: {e}")
        return {
            "total": 0,
            "approved": 0,
            "rejected": 0,
            "edited": 0,
            "unique_validated": 0,
            "gold_verified": 0,
        }


def load_user_gamification() -> dict:
    """Loads user points, level, and badge from local file."""
    if LOCAL_USER_STATS_PATH.exists():
        try:
            with open(LOCAL_USER_STATS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_user_gamification(data: dict):
    """Saves user points, level, and badge to local file."""
    try:
        LOCAL_USER_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOCAL_USER_STATS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Stats Error] Failed to save local gamification data: {e}")


def update_user_score(user_id: int, username: str, action: str) -> dict:
    """Updates user score and returns new level and badges."""
    stats = load_user_gamification()
    uid = str(user_id)

    if uid not in stats:
        stats[uid] = {
            "user_id": user_id,
            "username": username or f"User_{user_id}",
            "points": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "edited_count": 0,
            "total_reviews": 0,
            "rank": "🌱 Apprentice Linguist",
        }

    user = stats[uid]
    user["username"] = username or user.get("username")

    if action == "approved":
        user["points"] += 10
        user["approved_count"] += 1
    elif action == "rejected":
        user["points"] += 10
        user["rejected_count"] += 1
    elif action == "edited":
        user["points"] += 30  # High reward for contributing a correction!
        user["edited_count"] += 1

    user["total_reviews"] += 1

    # Tier Ranks
    pts = user["points"]
    if pts >= 500:
        user["rank"] = "👑 Horn AI Mastermind"
    elif pts >= 250:
        user["rank"] = "🥇 Gold Lexicographer"
    elif pts >= 100:
        user["rank"] = "🥈 Silver Contributor"
    elif pts >= 30:
        user["rank"] = "🥉 Bronze Validator"
    else:
        user["rank"] = "🌱 Apprentice Linguist"

    save_user_gamification(stats)
    return user


def get_leaderboard(limit: int = 5) -> list:
    """Returns top contributors sorted by points."""
    stats = load_user_gamification()
    sorted_users = sorted(stats.values(), key=lambda x: x.get("points", 0), reverse=True)
    return sorted_users[:limit]
