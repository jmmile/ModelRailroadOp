import sys
from pathlib import Path

# Add src folder to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.database.database import (
    initialize_database,
    SessionLocal,
)

from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot

from modelrailroadops.services.industry_service import IndustryService
from modelrailroadops.services.industry_track_service import (
    IndustryTrackService
)


def seed_cars():

    session = SessionLocal()

    try:

        session.query(Car).delete()
        session.commit()

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
                location="Yard C",
            ),
        ]

        session.add_all(cars)
        session.commit()

        print("Cars seeded successfully!")
        print(f"Added {len(cars)} cars.")

    finally:
        session.close()



def create_track_with_spots(
    industry_id,
    track_name,
    spot_count
):

    track = IndustryTrackService.add(
        industry_id=industry_id,
        name=track_name,
    )


    session = SessionLocal()

    try:

        existing = (
            session.query(Spot)
            .filter(
                Spot.track_id == track.id
            )
            .count()
        )

        if existing == 0:

            for number in range(1, spot_count + 1):

                session.add(
                    Spot(
                        track_id=track.id,
                        spot_number=number,
                    )
                )

            session.commit()


    finally:

        session.close()



def seed_industries():

    session = SessionLocal()

    try:

        print("Seeding industries...")

        session.query(Spot).delete()
        session.query(IndustryTrack).delete()
        session.query(Industry).delete()

        session.commit()


        industry = IndustryService.add(
            name="Wilhaeuser Lumber Company",
            railroad="SP",
            location="Portland",
            notes="Lumber loading facility",
        )


        create_track_with_spots(
            industry.id,
            "Storage Track",
            4,
        )


        create_track_with_spots(
            industry.id,
            "Main Loading Track",
            4,
        )


        print("Industries seeded successfully!")

    finally:

        session.close()



def seed_industry_tracks():

    print("Seeding industry tracks...")


    industries = IndustryService.get_all()

    industry_map = {
        industry.name: industry
        for industry in industries
    }


    tracks = [

        ("Wilhaeuser Lumber Company",
         "Receiving Track",
         4),

        ("Wilhaeuser Lumber Company",
         "Shipping Track",
         3),

    ]


    for industry_name, track_name, spot_count in tracks:


        industry = industry_map.get(
            industry_name
        )


        if industry is None:
            continue


        create_track_with_spots(
            industry.id,
            track_name,
            spot_count,
        )


    print("Industry tracks seeded successfully!")



if __name__ == "__main__":

    initialize_database()

    seed_cars()

    seed_industries()

    seed_industry_tracks()