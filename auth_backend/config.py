import os


SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "voicebox-secret-key-change-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "1440"))
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth.db")
DATABASE_URL: str = os.getenv("AUTH_DATABASE_URL", f"sqlite:///{_DB_PATH}")
