from pathlib import Path

from sqlalchemy import create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATABASE_FILE = PROJECT_ROOT / "data" / "railroad.db"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    echo=False,
)