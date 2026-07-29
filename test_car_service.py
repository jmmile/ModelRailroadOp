import sys
from pathlib import Path

# Add src folder to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.database.database import initialize_database, SessionLocal
from modelrailroadops.models.car import Car


def test_cars():
    session = SessionLocal()

    try:
        cars = session.query(Car).all()

        print("\nCars currently in database:")
        print("-" * 90)
        print(
            f"{'ID':<5}"
            f"{'Reporting':<12}"
            f"{'Number':<12}"
            f"{'Owner':<22}"
            f"{'Type':<25}"
            f"{'Status':<12}"
            f"{'Location':<20}"
        )
        print("-" * 90)

        for car in cars:
            print(
                f"{car.id:<5}"
                f"{car.reporting_mark:<12}"
                f"{car.number:<12}"
                f"{car.owner:<22}"
                f"{car.car_type:<25}"
                f"{car.status:<12}"
                f"{car.location:<20}"
            )

        print("-" * 90)
        print(f"{len(cars)} cars found.")

    finally:
        session.close()


if __name__ == "__main__":
    initialize_database()
    test_cars()