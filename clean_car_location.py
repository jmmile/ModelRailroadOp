
import sys
from pathlib import Path

# Add src folder to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car


# Cars whose location should be reset to Unassigned.
TARGET_CARS = [
    ("Lexington",),
    ("Seattle",),
    ("Cassette 1",),
]


def clean_car_locations():
    session = SessionLocal()

    try:
        cars = session.query(Car).filter(
            Car.location.in_([
                "Lexington",
                "Seattle",
                "Cassette 1",
            ])
        ).all()

        if not cars:
            print("No matching cars were found.")
            return

        print(f"Found {len(cars)} car(s) to clean:")
        print()

        for car in cars:
            print(
                f"  {car.reporting_mark} {car.number}: "
                f"{car.location} -> Unassigned"
            )

        print()

        for car in cars:
            car.location = "Unassigned"

        session.commit()

        print("Cleanup completed successfully.")
        print(f"Updated {len(cars)} car(s).")
        print()
        print("Only the location field was changed.")

    except Exception as exc:
        session.rollback()
        print("ERROR: No changes were saved.")
        print()
        print(exc)

    finally:
        session.close()


if __name__ == "__main__":
    clean_car_locations()
