"""Supabase client and gamified contributor stats for LISAN Telegram Bot."""

import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
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
    validated_text: Optional[str],
    status: str,
    reviewer_id: str,
    tg_username: str = "",
    notes: str = "",
) -> bool:
    """Inserts a community review record into Supabase PostgreSQL."""
    endpoint = f"{SUPABASE_URL}/rest/v1/community_validations"
    clean_handle = tg_username if tg_username.startswith("@") else (f"@{tg_username}" if tg_username else f"@{reviewer_id}")
    reviewer_parts = [f"tg:{clean_handle}", f"id:{reviewer_id}"]
    if notes:
        reviewer_parts.append(notes)
    full_note = " | ".join(reviewer_parts)

    payload = {
        "tuple_id": str(tuple_id),
        "domain": str(domain),
        "english_text": str(english_text),
        "target_lang": str(target_lang),
        "original_target": str(original_target),
        "validated_text": str(validated_text) if validated_text is not None else "[FLAGGED/REJECTED]",
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


def log_analytics_event(
    event_type: str,
    user_id: int = None,
    username: str = "",
    target_lang: str = "all",
    details: str = "",
) -> bool:
    """Logs a lightweight telemetry event into Supabase for live community analytics."""
    endpoint = f"{SUPABASE_URL}/rest/v1/community_validations"
    clean_handle = username if username.startswith("@") else (f"@{username}" if username else (f"@user_{user_id}" if user_id else "@anonymous"))
    notes = f"event:{event_type} | tg:{clean_handle}"
    if user_id:
        notes += f" | id:tg_{user_id}"
    if details:
        notes += f" | {details}"

    payload = {
        "tuple_id": "telemetry_event",
        "domain": "system",
        "english_text": f"Event: {event_type}",
        "target_lang": str(target_lang),
        "original_target": "system",
        "validated_text": f"event_{event_type}",
        "status": f"event:{event_type}",
        "reviewer_note": notes,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status in (200, 201)
    except Exception as e:
        print(f"[Supabase Telemetry Error] {e}")
        return False


def get_analytics_summary() -> dict:
    """Computes comprehensive live community analytics and telemetry from Supabase."""
    endpoint = f"{SUPABASE_URL}/rest/v1/community_validations?select=tuple_id,target_lang,status,reviewer_note,created_at"
    req = urllib.request.Request(
        endpoint,
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            rows = json.loads(response.read().decode("utf-8"))

            validations = [r for r in rows if r.get("status") in ("approved", "edited", "rejected")]
            events = [r for r in rows if str(r.get("status", "")).startswith("event:")]

            total_reviews = len(validations)
            approved = sum(1 for r in validations if r.get("status") in ("approved", "edited"))
            rejected = sum(1 for r in validations if r.get("status") == "rejected")
            edited = sum(1 for r in validations if r.get("status") == "edited")

            # Language breakdown
            lang_counts = {"amh": 0, "orm": 0, "tir": 0, "som": 0}
            for r in validations:
                l = r.get("target_lang")
                if l in lang_counts:
                    lang_counts[l] += 1

            # Unique contributors
            contributors = set()
            for r in validations:
                note = str(r.get("reviewer_note") or "")
                if "tg:@" in note:
                    u = note.split("tg:@")[1].split()[0].split("|")[0].strip()
                    contributors.add(f"@{u}")
                elif "tg:" in note:
                    u = note.split("|")[0].replace("tg:", "").strip()
                    if u and not u.startswith("tg_"):
                        contributors.add(u if u.startswith("@") else f"@{u}")

            # Bot sessions started
            bot_starts = sum(1 for e in events if e.get("status") == "event:bot_start")

            # 24h review velocity
            from datetime import datetime, timezone, timedelta
            reviews_24h = 0
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(hours=24)
            for r in validations:
                cat = r.get("created_at")
                if cat:
                    try:
                        dt = datetime.fromisoformat(cat.replace("Z", "+00:00"))
                        if dt >= cutoff:
                            reviews_24h += 1
                    except Exception:
                        pass

            approval_rate = round((approved / total_reviews * 100), 1) if total_reviews > 0 else 0.0

            return {
                "total_reviews": total_reviews,
                "approved": approved,
                "rejected": rejected,
                "edited": edited,
                "lang_counts": lang_counts,
                "unique_contributors": len(contributors),
                "bot_starts": bot_starts,
                "reviews_24h": reviews_24h,
                "approval_rate": approval_rate,
            }
    except Exception as e:
        print(f"[Supabase Error] Failed to get analytics summary: {e}")
        return {
            "total_reviews": 0,
            "approved": 0,
            "rejected": 0,
            "edited": 0,
            "lang_counts": {"amh": 0, "orm": 0, "tir": 0, "som": 0},
            "unique_contributors": 0,
            "bot_starts": 0,
            "reviews_24h": 0,
            "approval_rate": 0.0,
        }


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

                # Extract reviewer tags for deduplication
                if "tg:" in rev_note:
                    for part in rev_note.split("|"):
                        p = part.replace("tg:", "").replace("id:", "").strip()
                        if p:
                            scores[key]["reviewers"].add(p)
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
            validations = [r for r in rows if r.get("status") in ("approved", "edited", "rejected")]
            total = len(validations)
            approved = sum(1 for r in validations if r.get("status") in ("approved", "edited"))
            rejected = sum(1 for r in validations if r.get("status") == "rejected")
            edited = sum(1 for r in validations if r.get("status") == "edited")

            # Track unique tuple coverage and consensus
            tuple_approvals = {}
            for r in validations:
                tid = r.get("tuple_id")
                if tid and tid != "telemetry_event" and r.get("status") in ("approved", "edited"):
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
    clean_username = username if username.startswith("@") else f"@{username}"

    if uid not in stats:
        stats[uid] = {
            "user_id": user_id,
            "username": clean_username,
            "points": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "edited_count": 0,
            "total_reviews": 0,
            "rank": "🌱 Apprentice Linguist",
        }

    user = stats[uid]
    user["username"] = clean_username

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
    """Returns top contributors sorted by points, uniquely identified by Telegram username."""
    user_map = {}

    # 1. Fetch live reviews from Supabase
    endpoint = f"{SUPABASE_URL}/rest/v1/community_validations?select=status,reviewer_note"
    req = urllib.request.Request(
        endpoint,
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            rows = json.loads(response.read().decode("utf-8"))
            for r in rows:
                note = str(r.get("reviewer_note") or "")
                status = str(r.get("status") or "")

                username = None
                if "tg:@" in note:
                    raw = note.split("tg:@")[1].split()[0].split("|")[0].strip()
                    username = f"@{raw}"
                elif "tg:" in note:
                    raw = note.split("|")[0].replace("tg:", "").strip()
                    if raw and not raw.startswith("tg_"):
                        username = raw if raw.startswith("@") else f"@{raw}"

                if not username:
                    m = re.search(r"@([a-zA-Z0-9_]{3,32})", note)
                    if m and not m.group(1).startswith("tg_"):
                        username = f"@{m.group(1)}"

                if not username:
                    continue

                if username not in user_map:
                    user_map[username] = {
                        "username": username,
                        "points": 0,
                        "approved_count": 0,
                        "rejected_count": 0,
                        "edited_count": 0,
                        "total_reviews": 0,
                    }

                u = user_map[username]
                u["total_reviews"] += 1
                if status == "approved":
                    u["points"] += 10
                    u["approved_count"] += 1
                elif status == "rejected":
                    u["points"] += 10
                    u["rejected_count"] += 1
                elif status == "edited":
                    u["points"] += 30
                    u["edited_count"] += 1
    except Exception as e:
        print(f"[Supabase Error] get_leaderboard fetch error: {e}")

    # 2. Merge with local stats fallback
    local_stats = load_user_gamification()
    for uid, lu in local_stats.items():
        uname = lu.get("username", "")
        if uname:
            formatted_uname = uname if uname.startswith("@") else f"@{uname}"
            if formatted_uname not in user_map:
                user_map[formatted_uname] = {
                    "username": formatted_uname,
                    "points": lu.get("points", 0),
                    "approved_count": lu.get("approved_count", 0),
                    "rejected_count": lu.get("rejected_count", 0),
                    "edited_count": lu.get("edited_count", 0),
                    "total_reviews": lu.get("total_reviews", 0),
                }

    # 3. Assign tier ranks
    for u in user_map.values():
        pts = u["points"]
        if pts >= 500:
            u["rank"] = "👑 Horn AI Mastermind"
        elif pts >= 250:
            u["rank"] = "🥇 Gold Lexicographer"
        elif pts >= 100:
            u["rank"] = "🥈 Silver Contributor"
        elif pts >= 30:
            u["rank"] = "🥉 Bronze Validator"
        else:
            u["rank"] = "🌱 Apprentice Linguist"

    sorted_users = sorted(user_map.values(), key=lambda x: x["points"], reverse=True)
    return sorted_users[:limit]
