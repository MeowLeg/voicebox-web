"""Broadcast audio generator: TTS for body paragraphs + soundbite from video, merged in order."""

import io
import json
import logging
import subprocess
import tempfile
import time
import wave
from pathlib import Path

import requests

from config import TTS_BACKEND_URL

logger = logging.getLogger(__name__)


def _tts_generate(profile_id: str, text: str, language: str = "zh") -> bytes:
    """Call TTS backend to generate speech and return WAV bytes."""
    payload = {
        "profile_id": profile_id,
        "text": text,
        "language": language,
        "seed": 42,
    }
    logger.info(f"TTS request: {payload['text'][:50]}... → {TTS_BACKEND_URL}/generate")
    resp = requests.post(f"{TTS_BACKEND_URL}/generate", json=payload, timeout=30)
    if not resp.ok:
        detail = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
        raise RuntimeError(f"TTS生成请求失败: {detail}")
    try:
        data = resp.json()
    except Exception:
        body = resp.text[:200] if resp.text else "(empty response)"
        raise RuntimeError(f"TTS后端返回非JSON响应: {body}")
    gen_id = data.get("id")
    if not gen_id:
        raise RuntimeError(f"TTS后端未返回任务ID: {resp.text[:200]}")

    # Poll until complete (SSE stream)
    for _ in range(120):
        time.sleep(2)
        status_resp = requests.get(f"{TTS_BACKEND_URL}/generate/{gen_id}/status", timeout=10)
        if not status_resp.ok:
            continue
        raw = status_resp.text.strip()
        if not raw:
            continue
        # Parse SSE: each line is "data: {json}" or empty
        last_data = ""
        for line in raw.split("\n"):
            if line.startswith("data: "):
                last_data = line[6:]
        if not last_data:
            continue
        try:
            status = json.loads(last_data)
        except Exception:
            continue
        if status.get("status") == "completed":
            break
        if status.get("status") == "failed":
            raise RuntimeError(f"TTS generation failed for gen_id={gen_id}: {status.get('error', '')}")
    else:
        raise RuntimeError(f"TTS generation timeout for gen_id={gen_id}")

    # Download audio
    audio_resp = requests.get(f"{TTS_BACKEND_URL}/audio/{gen_id}", timeout=30)
    audio_resp.raise_for_status()
    return audio_resp.content


def _has_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def _extract_soundbite(video_url: str, start: float, end: float, tmp_dir: Path) -> bytes:
    """Extract audio segment from video using ffmpeg. Returns WAV bytes."""
    output_path = tmp_dir / f"soundbite_{start:.1f}_{end:.1f}.wav"
    duration = end - start
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-t", str(duration),
            "-i", video_url,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "44100", "-ac", "1",
            str(output_path),
        ],
        capture_output=True,
        timeout=120,
        check=True,
    )
    return output_path.read_bytes()


def _concat_wavs(wav_list: list[bytes], tmp_dir: Path) -> bytes:
    """Concatenate WAV files into a single WAV. Uses ffmpeg concat protocol if available,
    otherwise falls back to wave module."""
    if _has_ffmpeg() and len(wav_list) >= 1:
        # Write individual WAV files and build ffmpeg filter string
        inputs = []
        for i, wav_data in enumerate(wav_list):
            p = tmp_dir / f"seg_{i}.wav"
            p.write_bytes(wav_data)
            inputs.extend(["-i", str(p)])
        
        # Build concat filter with format normalization
        filter_parts = []
        for i in range(len(wav_list)):
            filter_parts.append(f"[{i}:a]aresample=44100:async=1[{i}n]")
        concat_inputs = "".join(f"[{i}n]" for i in range(len(wav_list)))
        filter_str = ";".join(filter_parts) + f";{concat_inputs}concat=n={len(wav_list)}:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=11[out]"

        output_path = tmp_dir / "broadcast.wav"
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_str,
            "-map", "[out]",
            "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, timeout=120, check=True)
        return output_path.read_bytes()
    else:
        frames = []
        params = None
        for wav_data in wav_list:
            with wave.open(io.BytesIO(wav_data), "rb") as wf:
                if params is None:
                    params = wf.getparams()
                frames.append(wf.readframes(wf.getnframes()))

        buf = io.BytesIO()
        with wave.open(buf, "wb") as out:
            out.setparams(params)
            for f in frames:
                out.writeframes(f)
        return buf.getvalue()


def generate_broadcast_audio(
    profile_id: str,
    paragraphs: list[dict],
    video_url: str | None = None,
    language: str = "zh",
) -> bytes:
    """Generate complete broadcast audio.

    Args:
        profile_id: Voice profile ID for TTS.
        paragraphs: List of {text, asrStartTime, asrEndTime}. Soundbite paragraphs
                    have asrStartTime != null.
        video_url: MP4 URL for soundbite extraction (required if any soundbite exists).
        language: TTS language.

    Returns:
        WAV audio bytes.
    """
    has_soundbite = any(p.get("asrStartTime") is not None for p in paragraphs)
    if has_soundbite and not video_url:
        raise ValueError("video_url is required when soundbite paragraphs exist")

    wav_parts: list[bytes] = []

    for p in paragraphs:
        if p.get("asrStartTime") is not None:
            start = float(p["asrStartTime"])
            end = float(p["asrEndTime"])
            with tempfile.TemporaryDirectory(prefix="broadcast_sb_") as tmp:
                wav = _extract_soundbite(video_url, start, end, Path(tmp))
                wav_parts.append(wav)
                logger.info(f"Soundbite extracted: {start:.1f}-{end:.1f}s, {len(wav)} bytes")
        else:
            text = p.get("text", "").strip()
            if not text:
                continue
            wav = _tts_generate(profile_id, text, language)
            wav_parts.append(wav)
            logger.info(f"TTS generated: {len(text)} chars → {len(wav)} bytes")

    if not wav_parts:
        raise ValueError("No audio generated")

    with tempfile.TemporaryDirectory(prefix="broadcast_concat_") as tmp:
        result = _concat_wavs(wav_parts, Path(tmp))
        logger.info(f"Broadcast audio merged: {len(result)} bytes")
        return result
