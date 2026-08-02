import sys
from pathlib import Path

from modelrailroadops.database import session
from modelrailroadops.services.industry_service import IndustryService
from modelrailroadops.services.industry_track_service import IndustryTrackService

# Add src folder to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.database.database import initialize_database, SessionLocal
from modelrailroadops.models.car import Car

from modelrailroadops.services.industry_service import IndustryService
from modelrailroadops.models.industry import Industry


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


def seed_industries():

    session = SessionLocal()

    try:
        print("Seeding industries...")

        industry = IndustryService.add(
            name="Wilhauser Lumber Company",
            railroad="SP",
            location="Portland",
            notes="Lumber loading facility"
        )

        IndustryTrackService.add(
            industry_id=industry.id,
            name="Main Loading Track",
            spots=6
        )

        IndustryTrackService.add(
            industry_id=industry.id,
            name="Storage Track",
            spots=4
        )

        print("Industries seeded successfully!")

    finally:
        session.close()



if __name__ == "__main__":
    initialize_database()
    seed_cars()
    seed_industries()