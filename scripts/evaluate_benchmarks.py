"""Automated Benchmark Suite for Ethiopian & Horn of Africa Languages.

Evaluates the offline translation pipeline against official gold benchmarks
(HornMT & FLORES-200) using SacreBLEU and chrF++.
"""

import argparse
import json
import os
from pathlib import Path
import sys
import time
import urllib.request

import sacrebleu

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BENCHMARK_DIR = Path(__file__).resolve().parent.parent / "data" / "benchmarks"
HORNMT_RAW_BASE = "https://raw.githubusercontent.com/asmelashteka/HornMT/main/data"
API_URL = "http://127.0.0.1:8000/translate/text"

# Language code mapping for HornMT / internal pipeline
LANG_MAP = {
    "amh": "amh",
    "orm": "orm",
    "som": "som",
    "tir": "tir",
    "eng": "eng",
}


def ensure_hornmt() -> dict[str, list[str]]:
    """Download and cache HornMT data files locally."""
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    horn_data: dict[str, list[str]] = {}

    for lang in LANG_MAP:
        target_file = BENCHMARK_DIR / f"hornmt_{lang}.txt"
        if not target_file.exists():
            url = f"{HORNMT_RAW_BASE}/{lang}.txt"
            print(f"Downloading HornMT {lang} from {url}...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp:
                content = resp.read().decode("utf-8")
                target_file.write_text(content, encoding="utf-8")
        
        lines = target_file.read_text(encoding="utf-8").splitlines()
        horn_data[lang] = [line.strip() for line in lines]
        print(f"  Loaded HornMT [{lang}]: {len(horn_data[lang])} sentences")

    return horn_data


def query_api(text: str, src: str, tgt: str) -> tuple[str, float]:
    """Query the running Uvicorn API server."""
    payload = json.dumps({"text": text, "src": src, "tgt": tgt}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        dt = time.perf_counter() - t0
        return res["translated_text"], dt


def evaluate_pair(
    src_lang: str,
    tgt_lang: str,
    src_sentences: list[str],
    ref_sentences: list[str],
    limit: int | None = None,
) -> dict:
    """Evaluate translation on a single language pair."""
    n = min(len(src_sentences), len(ref_sentences))
    if limit is not None and limit > 0:
        n = min(n, limit)

    hypotheses: list[str] = []
    references: list[str] = []
    latencies: list[float] = []

    print(f"\nEvaluating {src_lang.upper()} -> {tgt_lang.upper()} ({n} sentences)...")

    for i in range(n):
        src = src_sentences[i]
        ref = ref_sentences[i]
        if not src or not ref:
            continue

        try:
            hyp, dt = query_api(src, src_lang, tgt_lang)
            hypotheses.append(hyp)
            references.append(ref)
            latencies.append(dt)
        except Exception as e:
            print(f"  [Error @ sentence {i}]: {e}")
            continue

        if (i + 1) % 10 == 0 or (i + 1) == n:
            sys.stdout.write(f"\r  Progress: {i+1}/{n} ({(i+1)/n*100:.1f}%)")
            sys.stdout.flush()

    print()

    if not hypotheses:
        return {"error": "No successful translations"}

    # SacreBLEU computation
    bleu = sacrebleu.corpus_bleu(hypotheses, [references])
    # chrF++ computation (character n-grams + word n-grams)
    chrf = sacrebleu.corpus_chrf(hypotheses, [references], word_order=2)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    return {
        "src": src_lang,
        "tgt": tgt_lang,
        "samples_evaluated": len(hypotheses),
        "bleu": round(bleu.score, 2),
        "chrf_plus_plus": round(chrf.score, 2),
        "avg_latency_ms": round(avg_latency * 1000, 1),
        "sample_source": src_sentences[0] if src_sentences else "",
        "sample_reference": ref_sentences[0] if ref_sentences else "",
        "sample_hypothesis": hypotheses[0] if hypotheses else "",
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Ethiopian Translator Benchmarks")
    parser.add_argument("--limit", type=int, default=30, help="Number of benchmark sentences to evaluate per pair")
    parser.add_argument(
        "--pairs",
        type=str,
        default="amh-orm,amh-tir,amh-som,amh-eng,orm-amh,tir-amh,som-amh",
        help="Comma-separated list of src-tgt pairs",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(BENCHMARK_DIR / "benchmark_results.json"),
        help="Path to save evaluation output JSON",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Ethiopian & Horn of Africa MT Benchmark Suite (HornMT Gold Standard)")
    print("=" * 70)

    # 1. Ensure HornMT data is downloaded
    horn_data = ensure_hornmt()

    # 2. Parse language pairs
    pair_list = [p.strip().split("-") for p in args.pairs.split(",") if "-" in p]

    results = []
    print("\n" + "-" * 70)
    print(f"{'Pair':<12} | {'Samples':<8} | {'chrF++':<8} | {'BLEU':<8} | {'Avg Latency':<12}")
    print("-" * 70)

    for src_l, tgt_l in pair_list:
        if src_l not in horn_data or tgt_l not in horn_data:
            print(f"Skipping unknown pair: {src_l}->{tgt_l}")
            continue

        res = evaluate_pair(
            src_l,
            tgt_l,
            horn_data[src_l],
            horn_data[tgt_l],
            limit=args.limit,
        )
        results.append(res)

        print(
            f"{src_l.upper()} -> {tgt_l.upper():<5} | "
            f"{res.get('samples_evaluated', 0):<8} | "
            f"{res.get('chrf_plus_plus', 0):<8.2f} | "
            f"{res.get('bleu', 0):<8.2f} | "
            f"{res.get('avg_latency_ms', 0):<8.1f} ms"
        )

    print("-" * 70)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Benchmark results successfully saved to {output_path}")


if __name__ == "__main__":
    main()
