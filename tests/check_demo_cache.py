import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
from scripts.seed_demo_scenarios import RURAL_CLINIC_DIALOGUE, AXUM_TOURIST_DIALOGUE, text_hash

cache_dir = ROOT_DIR / "output_tts" / "cache"

print("--- RURAL CLINIC ---")
for i, item in enumerate(RURAL_CLINIC_DIALOGUE, 1):
    h_amh = text_hash("amh", item["amh"])
    h_orm = text_hash("orm", item["orm"])
    c_amh = (cache_dir / f"{h_amh}.wav").exists()
    c_orm = (cache_dir / f"{h_orm}.wav").exists()
    print(f"Turn {i:02d}: amh={c_amh} ({h_amh}), orm={c_orm} ({h_orm})")

print("\n--- AXUM TOURIST ---")
for i, item in enumerate(AXUM_TOURIST_DIALOGUE, 1):
    h_eng = text_hash("eng", item["eng"])
    h_tir = text_hash("tir", item["tir"])
    h_amh = text_hash("amh", item["amh"])
    c_eng = (cache_dir / f"{h_eng}.wav").exists()
    c_tir = (cache_dir / f"{h_tir}.wav").exists()
    c_amh = (cache_dir / f"{h_amh}.wav").exists()
    print(f"Turn {i:02d}: eng={c_eng} ({h_eng}), tir={c_tir} ({h_tir}), amh={c_amh} ({h_amh})")
