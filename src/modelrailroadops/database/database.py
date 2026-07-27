from pathlib import Path
import modelrailroadops.models.railroad
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from modelrailroadops.database.base import Base

# Database location
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATABASE_FILE = PROJECT_ROOT / "data" / "railroad.db"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    echo=False,
)

SessionLocal = sessionmaker(bind=engine)


def initialize_database():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)