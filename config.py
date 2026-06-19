import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SQLITE_PATH = INSTANCE_DIR / "chapa_do_bairro.db"

def build_database_uri():
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        return f"sqlite:///{DEFAULT_SQLITE_PATH}"

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    if database_url == "sqlite:///instance/chapa_do_bairro.db":
        return f"sqlite:///{DEFAULT_SQLITE_PATH}"

    if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
        relative_path = database_url.replace("sqlite:///", "", 1)
        absolute_path = BASE_DIR / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{absolute_path}"

    return database_url

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-me")
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    STORE_NAME = os.getenv("STORE_NAME", "Chapa do Bairro")
    STORE_SLOGAN = os.getenv("STORE_SLOGAN", "Chapa quente, hambúrguer de verdade.")
    WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "5535999999999")

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456")

    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
