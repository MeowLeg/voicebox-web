import ftplib
import logging
from pathlib import Path

from config import FTP_HOST, FTP_PORT, FTP_USER, FTP_PASSWORD, FTP_PATH, VOICEBOX_DATA_DIR

logger = logging.getLogger(__name__)


def upload_to_ftp(generation_id: str, remote_filename: str = "") -> str:
    """Upload a generation's audio file to the FTP server.

    Returns the remote file path on success, raises on failure.
    """
    if not FTP_HOST:
        raise RuntimeError("FTP 未配置，请在 start.sh 中设置 FTP_HOST / FTP_USER / FTP_PASSWORD")

    source = Path(VOICEBOX_DATA_DIR) / "generations" / f"{generation_id}.mp3"
    if not source.exists():
        source = Path(VOICEBOX_DATA_DIR) / "generations" / f"{generation_id}.wav"
    if not source.exists():
        raise FileNotFoundError(f"Audio file not found: {generation_id}")

    ext = source.suffix
    if remote_filename:
        remote_name = f"{remote_filename}{ext}"
    else:
        remote_name = f"{generation_id}{ext}"
    remote_path = f"{FTP_PATH.rstrip('/')}/{remote_name}"

    ftp = ftplib.FTP()
    ftp.encoding = "gbk"
    try:
        ftp.connect(FTP_HOST, FTP_PORT, timeout=30)
        ftp.login(FTP_USER, FTP_PASSWORD)

        # Some servers need this for UTF-8 filenames
        try:
            ftp.sendcmd("OPTS UTF8 ON")
        except Exception:
            pass

        if FTP_PATH and FTP_PATH != "/":
            try:
                ftp.cwd(FTP_PATH)
            except ftplib.error_perm:
                logger.warning("FTP CWD to %s failed, using root", FTP_PATH)

        # If filename has non-ASCII, try encoding it explicitly
        try:
            remote_name.encode("ascii")
        except UnicodeEncodeError:
            pass

        with open(source, "rb") as f:
            try:
                ftp.storbinary(f"STOR {remote_name}", f)
            except ftplib.error_perm:
                remote_name = f"{generation_id}{ext}"
                f.seek(0)
                ftp.storbinary(f"STOR {remote_name}", f)
                logger.warning("FTP filename fallback to: %s", remote_name)

        logger.info(f"FTP upload OK: {remote_path} ({source.stat().st_size} bytes)")
        return remote_path

    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()
