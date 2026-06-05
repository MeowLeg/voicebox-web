import os
import json
import logging
import threading
import time
import requests
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import TTS_BACKEND_URL, VOICEBOX_DATA_DIR
from database import SessionLocal, QueueTask, AudioRecord
from utils.asr_align import align_soundbites

POLL_INTERVAL = 2
MAX_POLL_SECONDS = 1800

logging.basicConfig(level=logging.INFO, format='[QueueWorker] %(message)s')
logger = logging.getLogger(__name__)


def parse_tts_response(res):
    ct = res.headers.get('content-type', '')
    if 'text/event-stream' in ct:
        text = res.text.strip()
        for line in text.split('\n'):
            if line.startswith('data:'):
                data_str = line[5:].strip()
                return json.loads(data_str)
    return res.json()


def _apply_speed(generation_id: str, speed: float) -> bool:
    source = Path(VOICEBOX_DATA_DIR) / "generations" / f"{generation_id}.wav"
    if not source.exists():
        logger.error(f"Source file not found: {source}")
        return False

    tmp = source.with_name(f"{generation_id}_speed.wav")

    from utils.speed_effects import change_speed_file

    try:
        change_speed_file(source, tmp, speed)
        os.replace(tmp, source)
        logger.info(f"Speed {speed}x applied in-place: {generation_id}")
        return True
    except Exception as e:
        logger.error(f"FFmpeg speed failed: {e}")
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        return False


def _convert_to_mp3(generation_id: str) -> bool:
    source = Path(VOICEBOX_DATA_DIR) / "generations" / f"{generation_id}.wav"
    if not source.exists():
        return False

    mp3_path = source.with_suffix(".mp3")
    from utils.speed_effects import convert_to_mp3

    try:
        convert_to_mp3(source, mp3_path)
        source.unlink()
        logger.info(f"Converted to MP3: {generation_id}")
        return True
    except Exception as e:
        logger.error(f"MP3 conversion failed: {e}")
        if mp3_path.exists():
            mp3_path.unlink(missing_ok=True)
        return False


class QueueWorker:
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"QueueWorker started, TTS backend: {TTS_BACKEND_URL}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("QueueWorker stopped")

    def _run(self):
        while self.running:
            try:
                self._process_next()
            except Exception as e:
                logger.error(f"Unhandled error: {e}", exc_info=True)
            time.sleep(1)

    def _process_next(self):
        db = SessionLocal()
        try:
            task = db.query(QueueTask).filter(
                QueueTask.status == "pending"
            ).order_by(
                QueueTask.created_at.asc()
            ).first()

            if not task:
                return

            task_id = task.id
            req_data = dict(task.request_data or {})
            requested_speed = req_data.get("speed")

            task.status = "processing"
            task.progress = 5.0
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Processing task {task_id}")

            task_type = req_data.get("task_type", "tts")
            if task_type == "asr_align":
                self._process_asr_align(task, req_data, db)
                return
            if task_type == "broadcast":
                self._process_broadcast(task, req_data, db)
                return

            tts_payload = {k: v for k, v in req_data.items() if k != "speed"}

            res = requests.post(
                f"{TTS_BACKEND_URL}/generate",
                json=tts_payload,
                timeout=30,
            )

            if res.status_code != 200:
                raise Exception(f"TTS后端返回 HTTP {res.status_code}: {res.text[:200]}")

            result = parse_tts_response(res)
            generation_id = result.get("id")
            if not generation_id:
                raise Exception("TTS后端未返回生成ID")

            task.voicebox_generation_id = generation_id
            task.status = "processing"
            task.progress = 10.0
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Task {task_id}: Generation started, ID={generation_id}")

            start_time = time.time()
            consecutive_errors = 0
            while time.time() - start_time < MAX_POLL_SECONDS:
                try:
                    status_res = requests.get(
                        f"{TTS_BACKEND_URL}/generate/{generation_id}/status",
                        timeout=(5, MAX_POLL_SECONDS),
                        stream=True,
                    )

                    if status_res.status_code != 200:
                        time.sleep(POLL_INTERVAL)
                        continue

                    gen_status = "generating"
                    for line in status_res.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            try:
                                status_data = json.loads(data_str)
                                gen_status = status_data.get("status", gen_status)
                                gen_progress = status_data.get("progress")
                                if gen_progress is not None:
                                    task.progress = max(task.progress, float(gen_progress))
                                    task.updated_at = datetime.now(timezone.utc)
                                    db.commit()
                            except json.JSONDecodeError:
                                continue

                    status_res.close()
                    consecutive_errors = 0
                    logger.info(f"Task {task_id}: Status={gen_status}")

                    if gen_status == "completed":
                        if requested_speed is not None and requested_speed != 1.0:
                            _apply_speed(generation_id, requested_speed)

                        _convert_to_mp3(generation_id)

                        audio_url = f"/voicebox-web/audio/{generation_id}"
                        task.status = "completed"
                        task.progress = 100.0
                        task.audio_url = audio_url
                        task.updated_at = datetime.now(timezone.utc)
                        db.commit()
                        logger.info(f"Task {task_id}: Completed!")

                        try:
                            record = AudioRecord(
                                id=str(uuid.uuid4()),
                                user_id=task.user_id,
                                voicebox_generation_id=generation_id,
                                profile_id=req_data.get("profile_id") or req_data.get("voice_id"),
                                text=req_data.get("text", ""),
                                title=req_data.get("title"),
                                language=req_data.get("language"),
                                audio_url=audio_url,
                                status="completed",
                                created_at=datetime.now(timezone.utc),
                            )
                            db.add(record)
                            db.commit()
                            logger.info(f"Task {task_id}: Audio record saved")
                        except Exception as e:
                            logger.error(f"Task {task_id}: Failed to save audio record: {e}")

                        return
                    elif gen_status == "failed":
                        raise Exception(status_data.get("error", "生成失败"))
                    elif gen_status == "not_found":
                        raise Exception("生成任务在TTS后端已不存在")

                except requests.RequestException:
                    consecutive_errors += 1
                    if consecutive_errors > 30:
                        raise Exception("TTS后端持续无响应")

                time.sleep(POLL_INTERVAL)

            raise Exception("生成超时")

        except Exception as e:
            logger.error(f"Task failed: {e}")
            try:
                task.status = "failed"
                task.error = str(e)
                task.updated_at = datetime.now(timezone.utc)
                db.commit()
            except Exception:
                pass

    def _process_broadcast(self, task, req_data, db):
        from utils.broadcast_audio import generate_broadcast_audio

        task_id = task.id
        paragraphs = req_data.get("paragraphs", [])
        video_url = req_data.get("video_url")
        profile_id = req_data.get("profile_id")
        language = req_data.get("language", "zh")

        if not paragraphs or not profile_id:
            task.status = "failed"
            task.error = "广播稿缺少段落或音色"
            db.commit()
            logger.error(f"Task {task_id}: Broadcast missing paragraphs/profile")
            return

        try:
            task.progress = 10.0
            db.commit()

            wav_bytes = generate_broadcast_audio(
                profile_id=profile_id,
                paragraphs=paragraphs,
                video_url=video_url,
                language=language,
            )

            # Save to voicebox data dir
            gen_id = str(uuid.uuid4())
            gen_dir = Path(VOICEBOX_DATA_DIR) / "generations"
            gen_dir.mkdir(parents=True, exist_ok=True)
            wav_path = gen_dir / f"{gen_id}.wav"
            wav_path.write_bytes(wav_bytes)

            # Convert to MP3
            from utils.speed_effects import convert_to_mp3
            convert_to_mp3(wav_path, wav_path.with_suffix(".mp3"))

            audio_url = f"/voicebox-web/audio/{gen_id}"
            task.voicebox_generation_id = gen_id
            task.status = "completed"
            task.progress = 100.0
            task.audio_url = audio_url
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Task {task_id}: Broadcast completed!")

            # Create audio record
            try:
                record = AudioRecord(
                    id=str(uuid.uuid4()),
                    user_id=task.user_id,
                    voicebox_generation_id=gen_id,
                    profile_id=profile_id,
                    text=task.request_data.get("title", "") or "广播稿",
                    title=task.request_data.get("title", ""),
                    language=language,
                    audio_url=audio_url,
                    status="completed",
                    engine=req_data.get("engine", ""),
                    model_size=req_data.get("model_size", ""),
                )
                db.add(record)
                db.commit()
            except Exception as e:
                logger.error(f"Task {task_id}: Failed to create audio record: {e}")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)[:500]
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.error(f"Task {task_id}: Broadcast failed: {e}")
        finally:
            db.close()

    def _process_asr_align(self, task, req_data, db):
        """后台处理 ASR 同期声对齐任务。"""
        video_url = req_data["video_url"]
        manuscript = req_data["manuscript"]
        model_size = req_data.get("model_size", "small")

        try:
            task.progress = 10.0
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"ASR align: extracting audio from {video_url[:80]}...")

            segments = align_soundbites(
                video_url=video_url,
                manuscript=manuscript,
                model_size=model_size,
            )

            task.progress = 90.0
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"ASR align: {len(segments)} segments aligned, finishing...")

            result_segments = []
            for s in segments:
                result_segments.append({
                    "original_text": s.original_text,
                    "start_time": int(round(s.start_time)),
                    "end_time": int(round(s.end_time)),
                    "matched_text": s.matched_text,
                    "confidence": s.confidence,
                    "clip_id": s.clip_id,
                    "audio_url": f"/audio/clip/{s.clip_id}" if s.clip_id else None,
                })

            req_data["result"] = {"segments": result_segments}
            task.request_data = req_data
            task.status = "completed"
            task.progress = 100.0
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"ASR align task {task.id}: completed")

        except Exception as e:
            logger.error(f"ASR align task failed: {e}")
            try:
                task.status = "failed"
                task.error = str(e)
                task.updated_at = datetime.now(timezone.utc)
                db.commit()
            except Exception:
                pass

    def _process_broadcast(self, task, req_data, db):
        from utils.broadcast_audio import generate_broadcast_audio

        task_id = task.id
        paragraphs = req_data.get("paragraphs", [])
        video_url = req_data.get("video_url")
        profile_id = req_data.get("profile_id")
        language = req_data.get("language", "zh")

        if not paragraphs or not profile_id:
            task.status = "failed"
            task.error = "广播稿缺少段落或音色"
            db.commit()
            logger.error(f"Task {task_id}: Broadcast missing paragraphs/profile")
            return

        try:
            task.progress = 10.0
            db.commit()

            wav_bytes = generate_broadcast_audio(
                profile_id=profile_id,
                paragraphs=paragraphs,
                video_url=video_url,
                language=language,
            )

            # Save to voicebox data dir
            gen_id = str(uuid.uuid4())
            gen_dir = Path(VOICEBOX_DATA_DIR) / "generations"
            gen_dir.mkdir(parents=True, exist_ok=True)
            wav_path = gen_dir / f"{gen_id}.wav"
            wav_path.write_bytes(wav_bytes)

            # Convert to MP3
            from utils.speed_effects import convert_to_mp3
            convert_to_mp3(wav_path, wav_path.with_suffix(".mp3"))

            audio_url = f"/voicebox-web/audio/{gen_id}"
            task.voicebox_generation_id = gen_id
            task.status = "completed"
            task.progress = 100.0
            task.audio_url = audio_url
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Task {task_id}: Broadcast completed!")

            # Create audio record
            try:
                record = AudioRecord(
                    id=str(uuid.uuid4()),
                    user_id=task.user_id,
                    voicebox_generation_id=gen_id,
                    profile_id=profile_id,
                    text=task.request_data.get("title", "") or "广播稿",
                    title=task.request_data.get("title", ""),
                    language=language,
                    audio_url=audio_url,
                    status="completed",
                    engine=req_data.get("engine", ""),
                    model_size=req_data.get("model_size", ""),
                )
                db.add(record)
                db.commit()
            except Exception as e:
                logger.error(f"Task {task_id}: Failed to create audio record: {e}")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)[:500]
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.error(f"Task {task_id}: Broadcast failed: {e}")