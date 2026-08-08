import sys
from pathlib import Path

# Add src folder to Python path
sys.path.insert(
    0,
    str(Path(__file__).parent / "src")
)


from modelrailroadops.database.database import (
    initialize_database,
    SessionLocal,
)

from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot

from modelrailroadops.services.industry_service import (
    IndustryService,
)

from modelrailroadops.services.industry_track_service import (
    IndustryTrackService,
)



def seed_cars():

    session = SessionLocal()

    try:

        print("Seeding cars...")


        session.query(Car).delete()

        session.commit()



        cars = [

            Car(
                reporting_mark="ATSF",
                number="123456",
                owner="Santa Fe",
                car_type="Boxcar",
                length=50,
                status="Available",
                location="Yard A",
            ),


            Car(
                reporting_mark="SP",
                number="987654",
                owner="Southern Pacific",
                car_type="Covered Hopper",
                length=55,
                status="Empty",
                location="Yard B",
            ),


            Car(
                reporting_mark="BN",
                number="555321",
                owner="Burlington Northern",
                car_type="Center Beam Flatcar",
                length=73,
                status="Loaded",
                location="Yard C",
            ),

        ]


        session.add_all(cars)

        session.commit()


        print(
            f"Cars seeded successfully! Added {len(cars)} cars."
        )


    finally:

        session.close()



def create_track_with_spots(
    industry_id,
    track_name,
    spot_count,
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

            for number in range(
                1,
                spot_count + 1
            ):

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



        industries = [

            (
                "Wilhaeuser Lumber Company",
                "SP",
                "Portland",
                "Lumber loading facility",
            ),


            (
                "Pacific Paper Mill",
                "BN",
                "Portland",
                "Paper products and pulp loading",
            ),


            (
                "Cascade Feed",
                "UP",
                "Portland",
                "Agricultural receiving facility",
            ),

        ]



        created = []


        for name, railroad, location, notes in industries:


            industry = IndustryService.add(

                name=name,

                railroad=railroad,

                location=location,

                notes=notes,

            )


            created.append(
                industry
            )



        # Lumber

        create_track_with_spots(
            created[0].id,
            "Receiving Track",
            4,
        )


        create_track_with_spots(
            created[0].id,
            "Shipping Track",
            4,
        )



        # Paper

        create_track_with_spots(
            created[1].id,
            "Pulp Track",
            3,
        )


        create_track_with_spots(
            created[1].id,
            "Boxcar Track",
            3,
        )



        # Feed

        create_track_with_spots(
            created[2].id,
            "Grain Track",
            5,
        )


        print(
            "Industries seeded successfully!"
        )


    finally:

        session.close()



if __name__ == "__main__":


    initialize_database()


    seed_cars()


    seed_industries()


    print(
        "Database seeding complete!"
    )