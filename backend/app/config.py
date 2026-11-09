import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

CONTENT_DIR = Path(os.getenv("CONTENT_DIR", BACKEND_DIR.parent / "content"))
DATA_DIR = Path(os.getenv("DATA_DIR", BACKEND_DIR / "data"))

# SQLite by default; set DATABASE_URL=postgresql+psycopg://user:pass@host/db for Postgres
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'app.db'}")

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5180").split(",") if o.strip()]
