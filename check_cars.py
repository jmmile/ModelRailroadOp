import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).parent / "src")
)

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car


with SessionLocal() as session:

    cars = session.query(Car).all()

    for car in cars:

        print(
            car.reporting_mark,
            car.number,
            "|",
            car.car_type,
            "|",
            car.length
        )