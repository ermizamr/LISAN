"""Downloader for Dataset.ET Hohe ASR model files."""
import sys
import os
from huggingface_hub import hf_hub_download

REPO_ID = "snapwre/hohe-asr-amharic"

def download_file(filename: str):
    print(f"--> Downloading {filename} from {REPO_ID}...", flush=True)
    try:
        path = hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            resume_download=True,
        )
        print(f"✓ Downloaded {filename} -> {path}", flush=True)
        return path
    except Exception as e:
        print(f"✗ Error downloading {filename}: {e}", file=sys.stderr, flush=True)
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Dataset.ET Hohe ASR Downloader")
    print("=" * 60)
    # Download weights first
    download_file("model.safetensors")
    print("Model weights ready!")
