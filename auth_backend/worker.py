import os
import json
import logging
import threading
import time
import requests
import uuid
from datetime import datetime, timezone

from database import SessionLocal, QueueTask, AudioRecord

TTS_BACKEND_URL = os.environ.get("TTS_BACKEND_URL", "http://61.153.213.238:17493")
POLL_INTERVAL = 2
MAX_POLL_SECONDS = 600

logging.basicConfig(level=logging.INFO, format='[QueueWorker] %(message)s')
logger = logging.getLogger(__name__)


def parse_tts_response(res):
    """Parse TTS backend response, handling both JSON and SSE formats."""
    ct = res.headers.get('content-type', '')
    if 'text/event-stream' in ct:
        text = res.text.strip()
        for line in text.split('\n'):
            if line.startswith('data:'):
                data_str = line[5:].strip()
                return json.loads(data_str)
    return res.json()


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
            req_data = task.request_data or {}

            task.status = "processing"
            task.progress = 5.0
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Processing task {task_id}")

            # Call TTS backend
            res = requests.post(
                f"{TTS_BACKEND_URL}/generate",
                json=req_data,
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

            # Poll for completion
            start_time = time.time()
            while time.time() - start_time < MAX_POLL_SECONDS:
                try:
                    status_res = requests.get(
                        f"{TTS_BACKEND_URL}/generate/{generation_id}/status",
                        timeout=10,
                    )

                    if status_res.status_code != 200:
                        time.sleep(POLL_INTERVAL)
                        continue

                    status_data = parse_tts_response(status_res)
                    gen_status = status_data.get("status", "")

                    if gen_status == "completed":
                        task.status = "completed"
                        task.progress = 100.0
                        task.audio_url = f"/voicebox-web/audio/{generation_id}"
                        task.duration = status_data.get("duration")
                        task.updated_at = datetime.now(timezone.utc)
                        db.commit()
                        logger.info(f"Task {task_id}: Completed!")

                        # Save to audio_records
                        try:
                            req_data = task.request_data or {}
                            record = AudioRecord(
                                id=str(uuid.uuid4()),
                                user_id=task.user_id,
                                voicebox_generation_id=generation_id,
                                profile_id=req_data.get("profile_id") or req_data.get("voice_id"),
                                text=req_data.get("text", ""),
                                language=req_data.get("language"),
                                audio_url=f"/voicebox-web/audio/{generation_id}",
                                duration=status_data.get("duration"),
                                seed=req_data.get("seed"),
                                instruct=req_data.get("instruct"),
                                engine=req_data.get("engine"),
                                model_size=req_data.get("model_size"),
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
                    else:
                        elapsed = time.time() - start_time
                        progress = min(10 + (elapsed / MAX_POLL_SECONDS) * 80, 90)
                        task.progress = progress
                        task.updated_at = datetime.now(timezone.utc)
                        db.commit()

                except requests.RequestException:
                    pass

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
        finally:
            db.close()
