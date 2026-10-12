"""
Zero-Fail End-to-End Verification Test
======================================
Tests all turns of Scenario 1 (Rural Clinic) and Scenario 2 (Axum Tourist)
against Translation Memory and verifies 100% on-device audio cache presence.
"""

import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from ai_pipeline.translation_memory import TranslationMemory
from scripts.seed_demo_scenarios import RURAL_CLINIC_DIALOGUE, AXUM_TOURIST_DIALOGUE, text_hash

def test_pipeline():
    print("=" * 75)
    print("LISAN ZERO-FAIL DEMO VERIFICATION SUITE")
    print("=" * 75)

    tm = TranslationMemory()
    cache_dir = ROOT_DIR / "output_tts" / "cache"

    failures = []
    total_checks = 0

    print("\n--- SCENARIO 1: Rural Clinic Triage (Amharic <-> Afaan Oromoo) ---")
    for i, turn in enumerate(RURAL_CLINIC_DIALOGUE, 1):
        amh = turn["amh"]
        orm = turn["orm"]

        # Check Amh -> Orm
        t0 = time.time()
        res_orm = tm.lookup(amh, "amh", "orm")
        dt_orm = (time.time() - t0) * 1000
        total_checks += 1
        if not res_orm or res_orm.score < 0.95:
            failures.append(f"Turn {i} Amh->Orm TM miss: '{amh}'")
            print(f"  [FAIL] Turn {i:02d} (Amh -> Orm) TM MISS")
        else:
            trans_orm = res_orm.target_text
            h_orm = text_hash("orm", trans_orm)
            audio_ok = (cache_dir / f"{h_orm}.wav").exists() and (cache_dir / f"{h_orm}.wav").stat().st_size > 500
            total_checks += 1
            if not audio_ok:
                failures.append(f"Turn {i} Orm audio missing: {h_orm}.wav")
                print(f"  [FAIL] Turn {i:02d} (Amh -> Orm) Audio file missing: {h_orm}.wav")
            else:
                print(f"  [PASS] Turn {i:02d} (Amh -> Orm): {dt_orm:.1f}ms | Audio: {h_orm}.wav OK")

        # Check Orm -> Amh
        t0 = time.time()
        res_amh = tm.lookup(orm, "orm", "amh")
        dt_amh = (time.time() - t0) * 1000
        total_checks += 1
        if not res_amh or res_amh.score < 0.95:
            failures.append(f"Turn {i} Orm->Amh TM miss: '{orm}'")
            print(f"  [FAIL] Turn {i:02d} (Orm -> Amh) TM MISS")
        else:
            trans_amh = res_amh.target_text
            h_amh = text_hash("amh", trans_amh)
            audio_ok = (cache_dir / f"{h_amh}.wav").exists() and (cache_dir / f"{h_amh}.wav").stat().st_size > 500
            total_checks += 1
            if not audio_ok:
                failures.append(f"Turn {i} Amh audio missing: {h_amh}.wav")
                print(f"  [FAIL] Turn {i:02d} (Orm -> Amh) Audio file missing: {h_amh}.wav")
            else:
                print(f"  [PASS] Turn {i:02d} (Orm -> Amh): {dt_amh:.1f}ms | Audio: {h_amh}.wav OK")

    print("\n--- SCENARIO 2: Axum Tourist (English <-> Tigrinya <-> Amharic) ---")
    for i, turn in enumerate(AXUM_TOURIST_DIALOGUE, 1):
        eng = turn["eng"]
        tir = turn["tir"]
        amh = turn["amh"]

        # Eng -> Tir
        t0 = time.time()
        res_tir = tm.lookup(eng, "eng", "tir")
        dt_tir = (time.time() - t0) * 1000
        total_checks += 1
        if not res_tir or res_tir.score < 0.95:
            failures.append(f"Turn {i} Eng->Tir TM miss: '{eng}'")
            print(f"  [FAIL] Turn {i:02d} (Eng -> Tir) TM MISS")
        else:
            h_tir = text_hash("tir", res_tir.target_text)
            audio_ok = (cache_dir / f"{h_tir}.wav").exists() and (cache_dir / f"{h_tir}.wav").stat().st_size > 500
            total_checks += 1
            if not audio_ok:
                failures.append(f"Turn {i} Tir audio missing: {h_tir}.wav")
                print(f"  [FAIL] Turn {i:02d} (Eng -> Tir) Audio missing: {h_tir}.wav")
            else:
                print(f"  [PASS] Turn {i:02d} (Eng -> Tir): {dt_tir:.1f}ms | Audio: {h_tir}.wav OK")

        # Tir -> Eng
        t0 = time.time()
        res_eng = tm.lookup(tir, "tir", "eng")
        dt_eng = (time.time() - t0) * 1000
        total_checks += 1
        if not res_eng or res_eng.score < 0.95:
            failures.append(f"Turn {i} Tir->Eng TM miss: '{tir}'")
            print(f"  [FAIL] Turn {i:02d} (Tir -> Eng) TM MISS")
        else:
            h_eng = text_hash("eng", res_eng.target_text)
            audio_ok = (cache_dir / f"{h_eng}.wav").exists() and (cache_dir / f"{h_eng}.wav").stat().st_size > 500
            total_checks += 1
            if not audio_ok:
                failures.append(f"Turn {i} Eng audio missing: {h_eng}.wav")
                print(f"  [FAIL] Turn {i:02d} (Tir -> Eng) Audio missing: {h_eng}.wav")
            else:
                print(f"  [PASS] Turn {i:02d} (Tir -> Eng): {dt_eng:.1f}ms | Audio: {h_eng}.wav OK")

        # Eng -> Amh
        t0 = time.time()
        res_amh = tm.lookup(eng, "eng", "amh")
        dt_amh = (time.time() - t0) * 1000
        total_checks += 1
        if not res_amh or res_amh.score < 0.95:
            failures.append(f"Turn {i} Eng->Amh TM miss: '{eng}'")
            print(f"  [FAIL] Turn {i:02d} (Eng -> Amh) TM MISS")
        else:
            h_amh = text_hash("amh", res_amh.target_text)
            audio_ok = (cache_dir / f"{h_amh}.wav").exists() and (cache_dir / f"{h_amh}.wav").stat().st_size > 500
            total_checks += 1
            if not audio_ok:
                failures.append(f"Turn {i} Amh audio missing: {h_amh}.wav")
                print(f"  [FAIL] Turn {i:02d} (Eng -> Amh) Audio missing: {h_amh}.wav")
            else:
                print(f"  [PASS] Turn {i:02d} (Eng -> Amh): {dt_amh:.1f}ms | Audio: {h_amh}.wav OK")

    print("\n" + "=" * 75)
    print(f"SUMMARY: {total_checks - len(failures)}/{total_checks} CHECKS PASSED")
    if not failures:
        print(">>> 100% ZERO-FAIL STATUS VERIFIED! Ready for live video demo. <<<")
    else:
        print(f">>> {len(failures)} FAILURES DETECTED! <<<")
        for f in failures:
            print("  -", f)
    print("=" * 75)

if __name__ == "__main__":
    test_pipeline()
