"""
Whisper 转写微服务 — 在 GPU 服务器上独立运行。
接收音频文件上传，返回词级时间戳。

启动:
    WHISPER_MODEL_SIZE=medium uvicorn main:app --host 0.0.0.0 --port 17500

环境变量:
    WHISPER_MODEL_SIZE  模型大小 (tiny/base/small/medium/large-v3)，默认 medium
    WHISPER_DEVICE      设备 (cuda/cpu)，默认 cuda
    WHISPER_COMPUTE_TYPE 计算类型 (float16/int8_float16/int8)，默认 float16
    WHISPER_CPU_THREADS CPU 线程数，仅 cpu 模式有效，默认 4
    HF_ENDPOINT         HuggingFace 镜像，如 https://hf-mirror.com
"""

import logging
import os
from pathlib import Path
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="[WhisperSvc] %(message)s")
logger = logging.getLogger(__name__)

# ── 模型加载（启动时一次性加载到 GPU） ──────────────────────────

MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "medium")
DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
CPU_THREADS = int(os.getenv("WHISPER_CPU_THREADS", "4"))
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "")

if HF_ENDPOINT:
    logger.info(f"HF_ENDPOINT={HF_ENDPOINT}")

from faster_whisper import WhisperModel

logger.info(f"Loading model '{MODEL_SIZE}' on {DEVICE} ({COMPUTE_TYPE})...")
model = WhisperModel(
    MODEL_SIZE,
    device=DEVICE,
    compute_type=COMPUTE_TYPE,
    cpu_threads=CPU_THREADS,
    num_workers=1,
    download_root=os.getenv("WHISPER_DOWNLOAD_ROOT", None),
    local_files_only=False,
)
logger.info("Model loaded ✓")

# ── FastAPI 应用 ───────────────────────────────────────────────

app = FastAPI(title="Whisper Transcription Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_SIZE, "device": DEVICE}


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form("zh"),
    beam_size: int = Form(1),
    best_of: int = Form(1),
):
    """上传音频文件，返回词级时间戳。

    返回格式:
    {
      "words": [{"word": "今天", "start": 0.12, "end": 0.34}, ...],
      "language": "zh",
      "duration": 120.5
    }
    """
    # 保存上传文件到临时目录
    suffix = Path(file.filename or "audio").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        logger.info(
            f"Transcribing '{file.filename}' ({os.path.getsize(tmp_path) / 1024:.0f} KB) "
            f"lang={language} beam={beam_size} best_of={best_of}"
        )

        segments, info = model.transcribe(
            tmp_path,
            language=language,
            word_timestamps=True,
            beam_size=beam_size,
            best_of=best_of,
            vad_filter=False,
            vad_parameters=None,
        )

        words = []
        for seg in segments:
            if seg.words:
                for w in seg.words:
                    word_text = w.word.strip()
                    if word_text:
                        words.append({
                            "word": word_text,
                            "start": round(w.start, 3),
                            "end": round(w.end, 3),
                        })

        logger.info(
            f"Done: {len(words)} words in {words[-1]['end'] if words else 0:.1f}s "
            f"(detected: {info.language}, duration: {info.duration:.1f}s)"
        )

        return {
            "words": words,
            "language": info.language,
            "duration": round(info.duration, 1),
        }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=17500)
