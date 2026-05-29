@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM  Whisper Transcription Service - Start Script for 4080S GPU
REM ============================================================

REM -- Model size: tiny / base / small / medium / large-v3
set WHISPER_MODEL_SIZE=medium

REM -- Device: cuda (GPU)
set WHISPER_DEVICE=cuda

REM -- Compute type: float16 (GPU) / int8_float16 / int8 (CPU)
set WHISPER_COMPUTE_TYPE=float16

REM -- CPU threads (ignored in CUDA mode)
set WHISPER_CPU_THREADS=4

REM -- HuggingFace mirror for China (uncomment if needed)
REM set HF_ENDPOINT=https://hf-mirror.com

REM -- Model download root (optional)
REM set WHISPER_DOWNLOAD_ROOT=D:\models\whisper

REM -- Service port
set WHISPER_PORT=17500

REM ============================================================

cd /d "%~dp0"

echo ========================================
echo  Whisper Transcription Service
echo  Model : %WHISPER_MODEL_SIZE%
echo  Device: %WHISPER_DEVICE% (%WHISPER_COMPUTE_TYPE%)
echo  Port  : %WHISPER_PORT%
echo ========================================
echo(

python --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+
    pause
    exit /b 1
)

python -c "import faster_whisper" >nul 2>nul
if errorlevel 1 (
    echo [WARN] faster_whisper not installed.
    echo       Run: pip install -r requirements.txt
    echo(
)

echo Starting uvicorn on port %WHISPER_PORT%...
python -m uvicorn main:app --host 0.0.0.0 --port %WHISPER_PORT%

pause
