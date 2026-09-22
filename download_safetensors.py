"""Robust resumable downloader for snapwre/hohe-asr-amharic model.safetensors."""
import os
import sys
import time
import requests

URL = "https://huggingface.co/snapwre/hohe-asr-amharic/resolve/main/model.safetensors"
SNAPSHOT_DIR = r"C:\Users\admin\.cache\huggingface\hub\models--snapwre--hohe-asr-amharic\snapshots\5c9eba39b2430df80d52a4dbc281b7350d034f5c"
TARGET_FILE = os.path.join(SNAPSHOT_DIR, "model.safetensors")
INCOMPLETE_FILE = TARGET_FILE + ".part"

TOTAL_SIZE = 2424524368  # 2.42 GB

def download():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    
    # Check if already complete
    if os.path.exists(TARGET_FILE) and os.path.getsize(TARGET_FILE) == TOTAL_SIZE:
        print(f"✓ model.safetensors already complete ({TOTAL_SIZE} bytes)")
        return

    # Check existing partial size
    existing = 0
    # Also check if the huggingface incomplete blob has data we can reuse
    hf_blob_incomplete = r"C:\Users\admin\.cache\huggingface\hub\models--snapwre--hohe-asr-amharic\blobs\9ec1ff28b669eb4a94d330e6879b1e0dbc6b1c451647f49805ed22856979fd77.incomplete"
    if not os.path.exists(INCOMPLETE_FILE) and os.path.exists(hf_blob_incomplete):
        blob_size = os.path.getsize(hf_blob_incomplete)
        if blob_size > 0:
            print(f"Reusing {blob_size / (1024*1024):.1f} MB from previous cache attempt...")
            import shutil
            shutil.copyfile(hf_blob_incomplete, INCOMPLETE_FILE)

    if os.path.exists(INCOMPLETE_FILE):
        existing = os.path.getsize(INCOMPLETE_FILE)

    print(f"Starting download of model.safetensors ({TOTAL_SIZE / (1024*1024):.1f} MB)...", flush=True)
    if existing > 0:
        print(f"Resuming from {existing / (1024*1024):.1f} MB ({existing / TOTAL_SIZE * 100:.1f}%)...", flush=True)

    headers = {}
    if existing > 0:
        headers["Range"] = f"bytes={existing}-"

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
            chunk_size = 2 * 1024 * 1024  # 2 MB chunks

            with open(INCOMPLETE_FILE, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        existing += len(chunk)
                        now = time.time()
                        if now - last_report > 3:  # report every 3 seconds
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
        print("✓ Download complete! model.safetensors is ready.", flush=True)
    else:
        print(f"Finished chunk: {existing} bytes.", flush=True)

if __name__ == "__main__":
    download()
