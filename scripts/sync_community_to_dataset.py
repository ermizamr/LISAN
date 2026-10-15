"""LISAN Community Consensus & Supabase Data Aggregator.

Pulls real-time crowd-sourced reviews from your Supabase PostgreSQL database:
1. Groups votes by tuple_id and target_lang.
2. Calculates community consensus metrics:
   - Total reviews per sentence
   - Number of 'approved' (GOOD) votes
   - Number of 'rejected' (BAD) votes
   - Number of 'edited' community corrections
   - Consensus Confidence Ratio: Approved / Total
3. Filters high-confidence community-validated pairs (Consensus >= 75%, Min Reviews >= 1).
4. Exports verified data directly into data/massive_dataset/community_verified.jsonl
   for automated LoRA fine-tuning.
"""

import sys
import json
import urllib.request
from collections import defaultdict
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT_DIR / "data" / "massive_dataset" / "community_verified.jsonl"

SUPABASE_URL = "https://xknxnycwrkffmxcwqxjs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhrbnhueWN3cmtmZm14Y3dxeGpzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIwODM5MTQsImV4cCI6MjEwNzY1OTkxNH0.5MgXgdhAtUggyNnCpL94EcjmR5JrAs74fiYK0BjUDaM"

NLLB_MAP = {
    "amh": "amh_Ethi",
    "orm": "gaz_Latn",
    "tir": "tir_Ethi",
    "som": "som_Latn",
    "eng": "eng_Latn",
}

def fetch_all_validations():
    """Fetches all rows from community_validations table via REST API."""
    url = f"{SUPABASE_URL}/rest/v1/community_validations?select=*"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
        return []

def aggregate_consensus(records, min_consensus: float = 0.70, min_votes: int = 1):
    """Groups votes per tuple and calculates approval consensus."""
    # Group by (tuple_id, target_lang)
    groups = defaultdict(list)
    for r in records:
        key = (r["tuple_id"], r["target_lang"])
        groups[key].append(r)

    scorecard = {
        "total_reviews": len(records),
        "unique_sentences_reviewed": len(groups),
        "promoted_to_training": 0,
        "rejected_quarantined": 0,
        "disputed_pending": 0,
    }

    verified_pairs = []

    print("=" * 80)
    print("      LISAN COMMUNITY VALIDATION TRACKER & CONSENSUS SCORECARD")
    print("=" * 80)
    print(f"Total Review Submissions in Supabase : {len(records):,}")
    print(f"Unique Sentences Evaluated           : {len(groups):,}")
    print("-" * 80)

    for (tuple_id, lang), votes in groups.items():
        # Exclude system health checks
        if tuple_id == "system_health_check":
            continue

        good_votes = sum(1 for v in votes if v["status"] in ("approved", "edited"))
        bad_votes = sum(1 for v in votes if v["status"] == "rejected")
        total_votes = good_votes + bad_votes

        consensus_ratio = good_votes / total_votes if total_votes > 0 else 0.0

        # Most recent validated text submitted by community
        latest_valid_text = votes[-1].get("validated_text") or votes[-1].get("original_target")
        english_text = votes[-1].get("english_text", "")
        domain = votes[-1].get("domain", "general")

        if consensus_ratio >= min_consensus and total_votes >= min_votes:
            # PROMOTED TO AI TRAINING
            scorecard["promoted_to_training"] += 1
            verified_pairs.append({
                "source": english_text,
                "target": latest_valid_text,
                "src_lang": "eng",
                "tgt_lang": lang,
                "src_nllb": NLLB_MAP["eng"],
                "tgt_nllb": NLLB_MAP[lang],
                "domain": domain,
                "confidence": round(min(1.0, 0.90 + (0.10 * consensus_ratio)), 2),
                "community_stats": {
                    "good_votes": good_votes,
                    "bad_votes": bad_votes,
                    "consensus_ratio": round(consensus_ratio, 2)
                },
                "source_dataset": "community_validated_gold"
            })
            # Also add reverse pair (Horn -> Eng)
            verified_pairs.append({
                "source": latest_valid_text,
                "target": english_text,
                "src_lang": lang,
                "tgt_lang": "eng",
                "src_nllb": NLLB_MAP[lang],
                "tgt_nllb": NLLB_MAP["eng"],
                "domain": domain,
                "confidence": round(min(1.0, 0.90 + (0.10 * consensus_ratio)), 2),
                "community_stats": {
                    "good_votes": good_votes,
                    "bad_votes": bad_votes,
                    "consensus_ratio": round(consensus_ratio, 2)
                },
                "source_dataset": "community_validated_gold"
            })
        elif bad_votes > good_votes:
            # QUARANTINED (BAD / REJECTED)
            scorecard["rejected_quarantined"] += 1
        else:
            # DISPUTED (Split votes, needs more reviewers)
            scorecard["disputed_pending"] += 1

    print(f"Promoted to AI Training (Consensus >= {int(min_consensus*100)}%) : {scorecard['promoted_to_training']:,} sentences ({len(verified_pairs):,} bidirectional pairs)")
    print(f"Quarantined / Rejected by Community        : {scorecard['rejected_quarantined']:,} sentences")
    print(f"Disputed (Split opinions, needs more votes): {scorecard['disputed_pending']:,} sentences")
    print("=" * 80)

    if verified_pairs:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for p in verified_pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        print(f"✓ Saved verified dataset to {OUTPUT_FILE}")

    return scorecard

if __name__ == "__main__":
    records = fetch_all_validations()
    aggregate_consensus(records)
