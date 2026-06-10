"""Local video library: FTP download + format conversion + local search."""

import logging
import os
import re
import subprocess
import uuid
from datetime import datetime, timedelta
from ftplib import FTP
from pathlib import Path

from sqlalchemy.orm import Session

from database import SessionLocal, LocalVideo

logger = logging.getLogger(__name__)

VIDEO_DIR = Path(os.path.expanduser("~/voicebox_videos"))
FTP_HOST = "192.168.6.200"
FTP_USER = "kjglb"
FTP_PASS = "kjglb@2026"

MAX_SIZE_MB = 50


def _get_ftp() -> FTP:
    ftp = FTP(FTP_HOST, timeout=30)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.encoding = 'gbk'
    return ftp


def _convert_to_mp4(src: Path, dst: Path) -> bool:
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(src),
                "-c:v", "libx264",
                "-crf", "28",
                "-preset", "fast",
                "-c:a", "aac",
                "-b:a", "64k",
                "-movflags", "+faststart",
                str(dst),
            ],
            capture_output=True,
            timeout=300,
            check=True,
        )
        return True
    except Exception as e:
        logger.error(f"FFmpeg conversion failed for {src}: {e}")
        return False


def _extract_title(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r'[\d_\-]+$', '', name)
    return name.strip()


def sync_videos():
    """Download videos from FTP for the last 2 days."""
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(2)]

        ftp = _get_ftp()
        try:
            for date_str in dates:
                # Try multiple date directory formats
                dir_formats = [date_str, date_str.replace("-", "")]
                ftp_dir = None
                for d in dir_formats:
                    try:
                        ftp.cwd(f"/{d}")
                        ftp_dir = d
                        break
                    except Exception:
                        pass
                if not ftp_dir:
                    logger.info(f"FTP dir for {date_str} not found, skipping")
                    continue

                files = ftp.nlst()
                for fname in files:
                    if fname.startswith("."):
                        continue

                    # Check if already downloaded (by date + original name or derived names)
                    base_stem = Path(fname).stem
                    existing = db.query(LocalVideo).filter(
                        LocalVideo.video_date == date_str,
                        (LocalVideo.file_name == fname) |
                        (LocalVideo.file_name == base_stem + ".mp4") |
                        (LocalVideo.file_name == base_stem + "_compressed.mp4")
                    ).first()
                    if existing:
                        logger.info(f"Skipping (already exists): {fname}")
                        continue

                    local_path = VIDEO_DIR / fname
                    target_path = local_path

                    with open(local_path, "wb") as f:
                        ftp.retrbinary(f"RETR {fname}", f.write)
                    logger.info(f"Downloaded: {fname}")

                    if not fname.lower().endswith(".mp4"):
                        mp4_path = local_path.with_suffix(".mp4")
                        if _convert_to_mp4(local_path, mp4_path):
                            local_path.unlink()
                            target_path = mp4_path
                            fname = mp4_path.name
                        else:
                            local_path.unlink()
                            continue

                    file_size_mb = target_path.stat().st_size / (1024 * 1024)
                    if file_size_mb > MAX_SIZE_MB:
                        compressed = target_path.with_stem(target_path.stem + "_compressed")
                        if _convert_to_mp4(target_path, compressed):
                            target_path.unlink()
                            target_path = compressed
                            fname = compressed.name

                    file_size = target_path.stat().st_size

                    record = LocalVideo(
                        id=str(uuid.uuid4()),
                        title=_extract_title(fname),
                        file_name=fname,
                        file_path=str(target_path.absolute()),
                        file_size=file_size,
                        video_date=date_str,
                    )
                    db.add(record)
                    db.commit()
                    logger.info(f"Saved: {fname} ({file_size / 1024 / 1024:.1f}MB)")

                ftp.cwd("/")
        finally:
            ftp.quit()
    finally:
        db.close()


def search_local(title: str) -> list[dict]:
    """Search local video library by title (fuzzy match)."""
    db = SessionLocal()
    try:
        keywords = title.strip().split()
        query = db.query(LocalVideo)
        for kw in keywords:
            query = query.filter(LocalVideo.title.ilike(f"%{kw}%"))
        results = query.order_by(LocalVideo.video_date.desc()).limit(20).all()

        return [
            {
                "name": r.file_name,
                "file_paths": [f"/articles/local-video/{r.file_name}"],
                "key_frame_path": None,
                "source": "local",
            }
            for r in results
        ]
    finally:
        db.close()
