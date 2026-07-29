import sys
from pathlib import Path

# Add src folder to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.database.database import initialize_database, SessionLocal
from modelrailroadops.models.car import Car


def seed_cars():
    session = SessionLocal()

    try:
        # Remove existing test cars
        session.query(Car).delete()

        cars = [
            Car(
                reporting_mark="ATSF",
                number="123456",
                owner="Santa Fe",
                car_type="Boxcar",
                status="Active",
                location="Yard A",
            ),
            Car(
                reporting_mark="SP",
                number="987654",
                owner="Southern Pacific",
                car_type="Covered Hopper",
                status="Active",
                location="Yard B",
            ),
            Car(
                reporting_mark="BN",
                number="555321",
                owner="Burlington Northern",
                car_type="Center Beam Flatcar",
                status="Active",
                location="Industry Track",
            ),
        ]

        session.add_all(cars)
        session.commit()

        print("Database seeded successfully!")
        print(f"Added {len(cars)} cars.")

    finally:
        session.close()


if __name__ == "__main__":
    initialize_database()
    seed_cars()