import os, sys, tempfile
hf_home = os.path.join(tempfile.gettempdir(), "hf_cache_direct")
os.environ["HF_HOME"] = hf_home
os.environ.pop("HF_ENDPOINT", None)
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.makedirs(hf_home, exist_ok=True)
print(f"HF_HOME={hf_home} (direct to huggingface.co)", flush=True)
from huggingface_hub import snapshot_download
try:
    path = snapshot_download("Systran/faster-whisper-medium", max_workers=1)
    print("OK:", path, flush=True)
except Exception as e:
    print(f"FAIL: {e}", flush=True)
    sys.exit(1)
