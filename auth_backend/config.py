import os

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "voicebox-secret-key-change-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "1440"))
_DB_PATH = os.path.join(BASE_DIR, "auth.db")
DATABASE_URL: str = os.getenv("AUTH_DATABASE_URL", f"sqlite:///{_DB_PATH}")

TTS_BACKEND_URL: str = os.getenv("TTS_BACKEND_URL", "http://127.0.0.1:17493")
VOICEBOX_DATA_DIR: str = os.getenv("VOICEBOX_DATA_DIR", os.path.expanduser("~/Documents/GitHub/voicebox/data"))

OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "http://192.168.102.217:8080/v1")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "Jh2044695")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "qwen/qwen3.6-27b")

HF_ENDPOINT: str = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")

FTP_HOST: str = os.getenv("FTP_HOST", "192.168.117.4")
FTP_PORT: int = int(os.getenv("FTP_PORT", "21023"))
FTP_USER: str = os.getenv("FTP_USER", "jmtrans")
FTP_PASSWORD: str = os.getenv("FTP_PASSWORD", "Zsgb@2047")
FTP_PATH: str = os.getenv("FTP_PATH", "/998")
