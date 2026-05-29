import os, sys
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
print("downloading...", flush=True)
from huggingface_hub import snapshot_download
try:
    path = snapshot_download("Systran/faster-whisper-medium")
    print("OK:", path, flush=True)
except Exception as e:
    print(f"FAIL: {e}", flush=True)
    sys.exit(1)
