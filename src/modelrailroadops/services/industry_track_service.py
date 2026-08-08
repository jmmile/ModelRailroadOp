#```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.car import Car


class IndustryTrackService:
    """
    Service methods for managing industry tracks.
    """

    @staticmethod
    def add(
        industry_id,
        name,
        spots=0,
    ):
        """
        Add a new industry track and create spots.
        """

        with SessionLocal() as session:

            existing = session.execute(
                select(IndustryTrack).where(
                    IndustryTrack.industry_id == industry_id,
                    IndustryTrack.name == name,
                )
            ).scalar_one_or_none()

            if existing:
                return existing

            track = IndustryTrack(
                industry_id=industry_id,
                name=name,
            )

            session.add(track)

            session.flush()

            for number in range(1, spots + 1):

                session.add(
                    Spot(
                        track_id=track.id,
                        spot_number=number,
                    )
                )

            session.commit()

            return IndustryTrackService.get_by_id(
                track.id
            )


    @staticmethod
    def update(
        track_id,
        name,
        spots,
    ):
        """
        Update an existing track.

        Adjusts the number of spots.
        Does not remove occupied spots.
        """

        with SessionLocal() as session:

            track = session.get(
                IndustryTrack,
                track_id
            )

            if track is None:
                return None

            track.name = name

            current_count = session.execute(
                select(Spot)
                .where(
                    Spot.track_id == track.id
                )
            ).scalars().all()

            current_count = len(
                current_count
            )

            #
            # Add spots
            #

            if spots > current_count:

                for number in range(
                    current_count + 1,
                    spots + 1
                ):

                    session.add(
                        Spot(
                            track_id=track.id,
                            spot_number=number,
                        )
                    )

            #
            # Remove spots
            #

            elif spots < current_count:

                remove_count = (
                    current_count - spots
                )

                removable_spots = (
                    session.execute(
                        select(Spot)
                        .where(
                            Spot.track_id == track.id
                        )
                        .order_by(
                            Spot.spot_number.desc()
                        )
                    )
                    .scalars()
                    .all()
                )

                removed = 0

                for spot in removable_spots:

                    occupied = (
                        session.execute(
                            select(Car)
                            .where(
                                Car.spot_id == spot.id
                            )
                        )
                        .scalar_one_or_none()
                    )

                    if occupied:
                        continue

                    session.delete(
                        spot
                    )

                    removed += 1

                    if removed == remove_count:
                        break

                if removed != remove_count:

                    session.rollback()

                    return None

            session.commit()

        return IndustryTrackService.get_by_id(
            track_id
        )


    @staticmethod
    def get_by_id(
        track_id
    ):
        """
        Return one track with related
        industry, spots, and spot cars loaded.
        """

        with SessionLocal() as session:

            return (
                session.execute(
                    select(IndustryTrack)
                    .options(
                        selectinload(
                            IndustryTrack.spots
                        ).selectinload(
                            Spot.car
                        ),

                        selectinload(
                            IndustryTrack.cars
                        ),

                        selectinload(
                            IndustryTrack.industry
                        ),
                    )
                    .where(
                        IndustryTrack.id == track_id
                    )
                )
                .scalars()
                .unique()
                .one_or_none()
            )


    @staticmethod
    def get_all():
        """
        Return all industry tracks with
        spots and their cars loaded.
        """

        with SessionLocal() as session:

            return (
                session.execute(
                    select(IndustryTrack)
                    .options(
                        selectinload(
                            IndustryTrack.spots
                        ).selectinload(
                            Spot.car
                        ),

                        selectinload(
                            IndustryTrack.cars
                        ),

                        selectinload(
                            IndustryTrack.industry
                        ),
                    )
                    .order_by(
                        IndustryTrack.name
                    )
                )
                .scalars()
                .unique()
                .all()
            )


    @staticmethod
    def get_by_industry(
        industry_id
    ):
        """
        Return tracks for an industry
        with spots and their cars loaded.
        """

        with SessionLocal() as session:

            return (
                session.execute(
                    select(IndustryTrack)
                    .options(
                        selectinload(
                            IndustryTrack.spots
                        ).selectinload(
                            Spot.car
                        ),

                        selectinload(
                            IndustryTrack.cars
                        ),

                        selectinload(
                            IndustryTrack.industry
                        ),
                    )
                    .where(
                        IndustryTrack.industry_id == industry_id
                    )
                    .order_by(
                        IndustryTrack.name
                    )
                )
                .scalars()
                .unique()
                .all()
            )


    @staticmethod
    def delete(
        track_id
    ):
        """
        Delete a track.

        Prevent deletion if a car is assigned.
        """

        with SessionLocal() as session:

            track = session.get(
                IndustryTrack,
                track_id
            )

            if track is None:
                return False

            occupied = (
                session.execute(
                    select(Car)
                    .where(
                        Car.track_id == track_id
                    )
                )
                .scalar_one_or_none()
            )

            if occupied:
                return False

            session.delete(
                track
            )

            session.commit()

            return True
#```
