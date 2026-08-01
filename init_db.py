import sys
from pathlib import Path

# Tell Python where the application package is
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.database.base import Base
from modelrailroadops.database.database import engine

# Import all models so SQLAlchemy knows about them
from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry

Base.metadata.create_all(bind=engine)

print("Database initialized successfully.")