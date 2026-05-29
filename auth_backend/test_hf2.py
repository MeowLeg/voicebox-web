import os, sys, tempfile
hf_home = os.path.join(tempfile.gettempdir(), "hf_cache_test")
os.environ["HF_HOME"] = hf_home
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.makedirs(hf_home, exist_ok=True)
print(f"HF_HOME={hf_home}", flush=True)
from huggingface_hub import snapshot_download
try:
    path = snapshot_download("Systran/faster-whisper-medium")
    print("OK:", path, flush=True)
except Exception as e:
    print(f"FAIL: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
