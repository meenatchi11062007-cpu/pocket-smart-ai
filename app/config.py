import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    APP_NAME = os.getenv("APP_NAME", "PocketSmart AI")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'pocketsmart.db').as_posix()}")
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))

settings = Settings()
UPLOAD_DIR = BASE_DIR / "app" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
