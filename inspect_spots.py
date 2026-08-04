import sys
from pathlib import Path

# Add src folder to Python path
sys.path.insert(
    0,
    str(Path(__file__).parent / "src")
)

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack


with SessionLocal() as session:

    industries = (
        session.execute(
            select(Industry)
            .options(
                selectinload(Industry.tracks)
                .selectinload(IndustryTrack.spots)
            )
            .order_by(
                Industry.name
            )
        )
        .scalars()
        .all()
    )


    for industry in industries:

        print()
        print(
            f"Industry: {industry.name}"
        )

        print(
            f"Location: {industry.location}"
        )


        for track in industry.tracks:

            print()
            print(
                f"  Track: {track.name}"
            )

            print(
                f"  Capacity: {len(track.spots)}"
            )


            for spot in track.spots:

                if spot.car:

                    occupied = (
                        f"{spot.car.reporting_mark} "
                        f"{spot.car.number}"
                    )

                else:

                    occupied = "Empty"


                print(
                    f"    Spot {spot.spot_number}: {occupied}"
                )