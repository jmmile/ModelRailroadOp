import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car


with SessionLocal() as session:
    cars = session.query(Car).filter(
        Car.reporting_mark == "UP",
        Car.number == "19999"
    ).all()

    print(f"Found {len(cars)} UP 19999 cars")

    for car in cars:
        session.delete(car)

    session.commit()

    print("Removed test duplicates")