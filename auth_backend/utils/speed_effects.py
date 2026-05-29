"""
Speech rate adjustment using FFmpeg atempo filter.

Implements the same technique used by H5 audio players:
- atempo filter for time-stretch without pitch change
- Chained atempo for speed ranges beyond 0.5x–2.0x
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_ATEMPO_MIN = 0.5
_ATEMPO_MAX = 2.0
_SPEED_MIN = 0.25
_SPEED_MAX = 4.0


def _build_atempo_filter_chain(speed: float) -> str:
    """Build FFmpeg atempo filter string for a given speed multiplier.

    The atempo filter supports 0.5–2.0 per instance.
    For speeds outside this range, we chain multiple atempo filters.

    Examples:
        speed=1.5  → "atempo=1.5"
        speed=3.0  → "atempo=2.0,atempo=1.5"
        speed=0.3  → "atempo=0.5,atempo=0.6"
    """
    if speed == 1.0:
        return "anull"

    remaining = speed
    filters: list[str] = []

    while remaining > _ATEMPO_MAX:
        filters.append(f"atempo={_ATEMPO_MAX}")
        remaining /= _ATEMPO_MAX

    while remaining < _ATEMPO_MIN:
        filters.append(f"atempo={_ATEMPO_MIN}")
        remaining /= _ATEMPO_MIN

    if remaining != 1.0:
        filters.append(f"atempo={remaining:.6f}")

    return ",".join(filters) if filters else "anull"


def change_speed(
    audio_bytes: bytes,
    speed: float,
    *,
    input_format: str = "wav",
    output_format: str = "wav",
    sample_rate: Optional[int] = None,
) -> bytes:
    """Change audio speed without altering pitch using FFmpeg atempo (bytes in/out).

    Uses subprocess + stdin/stdout piping — no temp files needed.
    """
    if speed <= 0:
        raise ValueError(f"speed must be positive, got {speed}")
    if speed < _SPEED_MIN or speed > _SPEED_MAX:
        raise ValueError(f"speed must be between {_SPEED_MIN} and {_SPEED_MAX}, got {speed}")

    if speed == 1.0:
        return audio_bytes

    filter_chain = _build_atempo_filter_chain(speed)

    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-f", input_format, "-i", "pipe:0",
        "-af", filter_chain,
    ]

    if sample_rate is not None:
        cmd.extend(["-ar", str(sample_rate)])

    cmd.extend(["-f", output_format, "pipe:1"])

    logger.info("Applying speed %.2fx with filter: %s", speed, filter_chain)

    try:
        result = subprocess.run(cmd, input=audio_bytes, capture_output=True, timeout=120)
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg is not installed. Install it with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg speed adjustment timed out")

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg failed (exit {result.returncode}): {stderr}")

    return result.stdout


def change_speed_file(
    input_path: str | Path,
    output_path: str | Path,
    speed: float,
) -> None:
    """Change audio speed using FFmpeg atempo (file to file).

    Direct file operation — no in-memory piping. Much faster for large files.
    """
    if speed <= 0:
        raise ValueError(f"speed must be positive, got {speed}")
    if speed < _SPEED_MIN or speed > _SPEED_MAX:
        raise ValueError(f"speed must be between {_SPEED_MIN} and {_SPEED_MAX}, got {speed}")

    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if speed == 1.0:
        import shutil
        shutil.copy2(input_path, output_path)
        return

    filter_chain = _build_atempo_filter_chain(speed)

    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-i", str(input_path),
        "-af", filter_chain,
        "-f", "wav",
        "-y",
        str(output_path),
    ]

    logger.info("Speed %.2fx: %s → %s", speed, input_path.name, output_path.name)

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg is not installed. Install it with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg speed adjustment timed out")

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg failed (exit {result.returncode}): {stderr}")


def stream_speed_from_file(
    input_path: str | Path,
    speed: float,
) -> subprocess.Popen:
    """Spawn FFmpeg subprocess that reads a file, applies speed, and writes WAV to stdout.

    Returns a Popen object whose stdout can be streamed directly.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if speed <= 0:
        raise ValueError(f"speed must be positive, got {speed}")
    if speed < _SPEED_MIN or speed > _SPEED_MAX:
        raise ValueError(f"speed must be between {_SPEED_MIN} and {_SPEED_MAX}, got {speed}")

    filter_chain = _build_atempo_filter_chain(speed)

    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-i", str(input_path),
        "-af", filter_chain,
        "-f", "wav",
        "pipe:1",
    ]

    logger.info("Streaming speed %.2fx from: %s", speed, input_path.name)

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg is not installed. Install it with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
        )

    return proc


def get_speed_range() -> dict:
    return {
        "min": _SPEED_MIN,
        "max": _SPEED_MAX,
        "default": 1.0,
        "step": 0.05,
    }


def convert_to_mp3(input_path: str | Path, output_path: str | Path, bitrate: str = "128k") -> None:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-i", str(input_path),
        "-codec:a", "libmp3lame",
        "-b:a", bitrate,
        "-y",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, timeout=120)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg MP3 conversion failed: {stderr}")
