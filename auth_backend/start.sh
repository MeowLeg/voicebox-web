#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

unset HF_ENDPOINT
unset HTTP_PROXY
unset HTTPS_PROXY
unset ALL_PROXY

# ── Whisper GPU 推理服务（4080S，取消注释启用远程推理）────
export WHISPER_SERVICE_URL=http://192.168.102.217:17500
export WHISPER_SERVICE_TIMEOUT=600
export WHISPER_BEAM_SIZE=1
export WHISPER_BEST_OF=1

export PYTHONPATH="$DIR"
export DYLD_LIBRARY_PATH="$DIR/venv/lib/python3.13/site-packages/av/.dylibs:$DYLD_LIBRARY_PATH"
export HF_HOME="/tmp/hf_cache"
source "$DIR/venv/bin/activate"

exec python -m uvicorn main:app --port 17494 --host 0.0.0.0
