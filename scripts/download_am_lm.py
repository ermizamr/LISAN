"""Download official Dataset.ET Hohe ASR 5-gram Language Model (am-5gram.bin)."""
import os
import sys
import time
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "https://huggingface.co/snapwre/hohe-asr-amharic/resolve/main/lm/am-5gram.bin"
SNAPSHOT_DIR = r"C:\Users\admin\.cache\huggingface\hub\models--snapwre--hohe-asr-amharic\snapshots\5c9eba39b2430df80d52a4dbc281b7350d034f5c\lm"
TARGET_FILE = os.path.join(SNAPSHOT_DIR, "am-5gram.bin")
INCOMPLETE_FILE = TARGET_FILE + ".part"
TOTAL_SIZE = 538297561  # 538.3 MB

def download():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    if os.path.exists(TARGET_FILE) and os.path.getsize(TARGET_FILE) == TOTAL_SIZE:
        print(f"✓ am-5gram.bin already complete ({TOTAL_SIZE} bytes)")
        return

    existing = 0
    if os.path.exists(INCOMPLETE_FILE):
        existing = os.path.getsize(INCOMPLETE_FILE)

    print(f"Starting download of am-5gram.bin ({TOTAL_SIZE / (1024*1024):.1f} MB)...", flush=True)
    if existing > 0:
        print(f"Resuming from {existing / (1024*1024):.1f} MB ({existing / TOTAL_SIZE * 100:.1f}%)...", flush=True)

    max_retries = 10
    retry_count = 0

    while existing < TOTAL_SIZE and retry_count < max_retries:
        try:
            headers = {"Range": f"bytes={existing}-"} if existing > 0 else {}
            response = requests.get(URL, headers=headers, stream=True, timeout=30)

            mode = "ab" if existing > 0 and response.status_code == 206 else "wb"
            if mode == "wb":
                existing = 0

            last_report = time.time()
            chunk_size = 2 * 1024 * 1024

            with open(INCOMPLETE_FILE, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        existing += len(chunk)
                        now = time.time()
                        if now - last_report > 3:
                            pct = (existing / TOTAL_SIZE) * 100
                            mb = existing / (1024 * 1024)
                            total_mb = TOTAL_SIZE / (1024 * 1024)
                            print(f"Progress: {mb:.1f} / {total_mb:.1f} MB ({pct:.1f}%)", flush=True)
                            last_report = now

            if existing >= TOTAL_SIZE:
                break

        except Exception as e:
            retry_count += 1
            print(f"Network glitch ({e}), retrying {retry_count}/{max_retries} in 3s...", flush=True)
            time.sleep(3)
            if os.path.exists(INCOMPLETE_FILE):
                existing = os.path.getsize(INCOMPLETE_FILE)

    if os.path.exists(INCOMPLETE_FILE) and os.path.getsize(INCOMPLETE_FILE) >= TOTAL_SIZE:
        if os.path.exists(TARGET_FILE):
            os.remove(TARGET_FILE)
        os.rename(INCOMPLETE_FILE, TARGET_FILE)
        print("✓ Download complete! am-5gram.bin is ready.", flush=True)
    else:
        print(f"Finished chunk: {existing} bytes.", flush=True)

if __name__ == "__main__":
    download()
