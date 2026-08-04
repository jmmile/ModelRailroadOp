import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.database.database import SessionLocal

# Import all models so SQLAlchemy can resolve relationships
from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot


session = SessionLocal()

cars = session.query(Car).all()

for car in cars:
    print()
    print(f"{car.reporting_mark} {car.number}")
    print(f"Industry: {car.industry}")
    print(f"Track: {car.track}")
    print(f"Spot: {car.spot}")

session.close()