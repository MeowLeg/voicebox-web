"""
电视新闻同期声 ASR 对齐模块

流程：
1. 下载视频 → 用 FFmpeg 提取音频 (16kHz mono WAV)
2. 用 faster_whisper 转写（词级时间戳，跳过 VAD/对齐）
3. 从新闻稿中提取【同期声】文本段
4. 模糊匹配，定位每段同期声的起止时间
"""

import logging
import os
import re
import subprocess
import tempfile
import uuid
import warnings
from dataclasses import dataclass
from pathlib import Path
from difflib import SequenceMatcher

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message=".*torchcodec.*")
warnings.filterwarnings("ignore", message=".*libtorchcodec.*")

logger = logging.getLogger(__name__)


@dataclass
class AlignedSegment:
    original_text: str
    start_time: float
    end_time: float
    matched_text: str
    confidence: float
    clip_id: str | None = None


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float


_SOUNDBITE_PATTERN = re.compile(r"【同期声】\s*\n?(.*?)(?=【[^】]+】|$)", re.DOTALL)


def extract_soundbites(manuscript: str) -> list[str]:
    matches = _SOUNDBITE_PATTERN.findall(manuscript)
    results: list[str] = []
    for match in matches:
        cleaned = re.sub(r"\s+", " ", match.strip())
        if cleaned:
            results.append(cleaned)
    return results


def download_video(video_url: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "video.mp4"
    logger.info(f"Downloading video: {video_url[:100]}...")
    resp = requests.get(video_url, stream=True, timeout=300, verify=False)
    resp.raise_for_status()
    total = 0
    with open(video_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            f.write(chunk)
            total += len(chunk)
    logger.info(f"Downloaded {total / 1024 / 1024:.1f} MB -> {video_path}")
    return video_path


def extract_audio_from_url(video_url: str, output_dir: Path) -> Path:
    """直接从 URL 提取音频流，跳过完整视频下载。"""
    audio_path = output_dir / "audio.wav"
    cmd = [
        "ffmpeg", "-y",
        "-i", video_url,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        "-loglevel", "error",
        str(audio_path),
    ]
    logger.info("Extracting audio directly from URL...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")
    logger.info(f"Audio extracted -> {audio_path}")
    return audio_path


def extract_audio(video_path: Path, output_dir: Path) -> Path:
    audio_path = output_dir / "audio.wav"
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        "-loglevel", "error",
        str(audio_path),
    ]
    logger.info("Extracting audio with FFmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    logger.info(f"Audio extracted -> {audio_path}")
    return audio_path


WHISPER_SERVICE_URL = os.getenv("WHISPER_SERVICE_URL", "")


def transcribe_audio(audio_path: Path, model_size: str = "small") -> list[WordTimestamp]:
    """转写音频，根据 WHISPER_SERVICE_URL 自动选择本地或远程推理。"""
    if WHISPER_SERVICE_URL:
        return _transcribe_remote(audio_path, model_size)
    else:
        return _transcribe_local(audio_path, model_size)


def _transcribe_remote(audio_path: Path, model_size: str) -> list[WordTimestamp]:
    """通过 HTTP 调用远程 Whisper GPU 服务。"""
    import requests as req_lib

    beam_size = int(os.getenv("WHISPER_BEAM_SIZE", "1"))
    best_of = int(os.getenv("WHISPER_BEST_OF", "1"))
    timeout = int(os.getenv("WHISPER_SERVICE_TIMEOUT", "600"))

    file_size_mb = audio_path.stat().st_size / 1024 / 1024
    logger.info(f"Uploading {file_size_mb:.1f} MB to {WHISPER_SERVICE_URL}/transcribe ...")

    with open(audio_path, "rb") as f:
        resp = req_lib.post(
            f"{WHISPER_SERVICE_URL}/transcribe",
            files={"file": (audio_path.name, f, "audio/wav")},
            data={
                "language": "zh",
                "beam_size": str(beam_size),
                "best_of": str(best_of),
            },
            timeout=timeout,
        )

    if resp.status_code != 200:
        detail = resp.text[:300]
        raise RuntimeError(f"Remote whisper service returned {resp.status_code}: {detail}")

    data = resp.json()
    words = [
        WordTimestamp(word=w["word"], start=w["start"], end=w["end"])
        for w in data.get("words", [])
    ]

    logger.info(
        f"Remote transcribed {len(words)} words in {words[-1].end if words else 0:.1f}s "
        f"(language: {data.get('language')}, duration: {data.get('duration', 0):.1f}s)"
    )
    return words


def _transcribe_local(audio_path: Path, model_size: str) -> list[WordTimestamp]:
    """本地 CPU/GPU 推理。"""
    hf_endpoint = os.getenv("HF_ENDPOINT", "")
    if hf_endpoint:
        logger.info(f"HF_ENDPOINT={hf_endpoint} (using mirror)")

    from faster_whisper import WhisperModel

    # faster_whisper 底层 ctranslate2 只支持 cpu/cuda
    device = "cpu"
    compute_type = "int8"
    cpu_threads = int(os.getenv("WHISPER_CPU_THREADS", "8"))
    force_device = os.getenv("WHISPER_DEVICE", "")
    if force_device:
        device = force_device
        compute_type = "float16" if force_device == "cuda" else "int8"

    logger.info(
        f"faster_whisper device={device}, compute_type={compute_type}, "
        f"model={model_size}, threads={cpu_threads}"
    )

    model = WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type,
        cpu_threads=cpu_threads,
        num_workers=1,
        download_root=os.getenv("WHISPER_DOWNLOAD_ROOT", None),
        local_files_only=False,
    )

    beam_size = int(os.getenv("WHISPER_BEAM_SIZE", "1"))
    best_of = int(os.getenv("WHISPER_BEST_OF", "1"))
    segments, info = model.transcribe(
        str(audio_path),
        language="zh",
        word_timestamps=True,
        beam_size=beam_size,
        best_of=best_of,
        vad_filter=False,
        vad_parameters=None,
    )

    words: list[WordTimestamp] = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                word_text = w.word.strip()
                if word_text:
                    words.append(WordTimestamp(word=word_text, start=w.start, end=w.end))

    logger.info(
        f"Transcribed {len(words)} words in {words[-1].end if words else 0:.1f}s "
        f"(detected: {info.language}, duration: {info.duration:.1f}s)"
    )
    return words


def _clean_text(text: str) -> str:
    cleaned = re.sub(r"[^\u4e00-\u9fff\u3400-\u4dbf\w]", "", text)
    return cleaned.lower().strip()


def _sliding_window_match(
    target_clean: str,
    words: list[WordTimestamp],
    min_match_ratio: float = 0.4,
) -> tuple[int, int, float] | None:
    n_words = len(words)
    if n_words == 0 or not target_clean:
        return None

    word_texts = [_clean_text(w.word) for w in words]
    full_text = "".join(word_texts)

    idx = full_text.find(target_clean)
    if idx != -1:
        char_pos = 0
        start_word = 0
        end_word = n_words - 1
        for i, wt in enumerate(word_texts):
            if char_pos <= idx < char_pos + len(wt):
                start_word = i
            if char_pos <= idx + len(target_clean) <= char_pos + len(wt):
                end_word = i
                break
            char_pos += len(wt)
        if end_word >= start_word:
            return (start_word, end_word, 1.0)

    target_len = len(target_clean)
    avg_word_len = max(1, sum(len(w) for w in word_texts) // max(1, n_words))
    window_words = max(2, min(n_words, int(target_len / max(1, avg_word_len)) * 2))
    min_end_skip = max(1, int(target_len / max(1, avg_word_len)) // 2)

    # 复用 SequenceMatcher 对象 + 预计算累积字符串避免每次 join
    prefix_cumsum = [0]
    for wt in word_texts:
        prefix_cumsum.append(prefix_cumsum[-1] + len(wt))
    full_text_joined = "".join(word_texts)

    sm = SequenceMatcher(None, target_clean, "")
    best_ratio = 0.0
    best_start = 0
    best_end = 0
    threshold = min_match_ratio
    for start in range(n_words):
        for end in range(start + min_end_skip, min(n_words, start + window_words + 1)):
            segment = full_text_joined[prefix_cumsum[start]:prefix_cumsum[end]]
            sm.set_seq2(segment)
            if sm.quick_ratio() < threshold:
                continue
            ratio = sm.ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_start = start
                best_end = end - 1
                threshold = max(threshold, best_ratio)

    if best_ratio >= min_match_ratio:
        return (best_start, best_end, best_ratio)
    return None


def align_soundbites(
    video_url: str,
    manuscript: str,
    model_size: str = "small",
    work_dir: str | None = None,
) -> list[AlignedSegment]:
    soundbites = extract_soundbites(manuscript)
    if not soundbites:
        logger.warning("No soundbites found in manuscript")
        return []

    logger.info(f"Found {len(soundbites)} soundbite(s)")

    if work_dir:
        base_dir = Path(work_dir)
    else:
        base_dir = Path(tempfile.mkdtemp(prefix="asr_align_"))
    base_dir.mkdir(parents=True, exist_ok=True)

    try:
        audio_path = extract_audio_from_url(video_url, base_dir)
        words = transcribe_audio(audio_path, model_size=model_size)

        # 准备持久化 clip 目录
        clips_dir = Path(os.getenv("VOICEBOX_DATA_DIR", os.path.expanduser("~/Documents/GitHub/voicebox/data"))) / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)

        import time as _time

        results: list[AlignedSegment] = []
        _clip_total_t = 0.0
        _match_total_t = 0.0
        for sb in soundbites:
            clean = _clean_text(sb)
            _t0 = _time.time()
            match = _sliding_window_match(clean, words)
            _dt = _time.time() - _t0
            _match_total_t += _dt
            if match:
                start_idx, end_idx, ratio = match
                start_s = words[start_idx].start
                end_s = words[end_idx].end

                clip_id = str(uuid.uuid4())
                clip_path = clips_dir / f"{clip_id}.wav"
                clip_cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(start_s),
                    "-to", str(end_s),
                    "-i", str(audio_path),
                    "-c", "copy",
                    "-loglevel", "error",
                    str(clip_path),
                ]
                _t0 = _time.time()
                clip_result = subprocess.run(clip_cmd, capture_output=True, text=True)
                _dt = _time.time() - _t0
                _clip_total_t += _dt
                if clip_result.returncode != 0:
                    logger.warning(f"  Clip FAIL ({_dt:.3f}s): {clip_result.stderr.strip()}")
                    clip_id_used = None
                else:
                    clip_id_used = clip_id
                    logger.info(f"  Clip saved ({_dt:.3f}s): {clip_path}")

                results.append(AlignedSegment(
                    original_text=sb,
                    start_time=start_s,
                    end_time=end_s,
                    matched_text=" ".join(w.word for w in words[start_idx:end_idx + 1]),
                    confidence=round(ratio, 4),
                    clip_id=clip_id_used,
                ))
                logger.info(f"  Matched [{start_s:.1f}s-{end_s:.1f}s] ratio={ratio:.3f}")
            else:
                results.append(AlignedSegment(sb, 0.0, 0.0, "", 0.0))
                logger.warning(f"  No match: \"{sb[:40]}...\"")

        logger.info(f"  Match total: {_match_total_t:.3f}s | Clip total: {_clip_total_t:.3f}s")

        return results
    finally:
        if work_dir is None:
            import shutil
            shutil.rmtree(base_dir, ignore_errors=True)