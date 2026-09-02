#```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.industry import Industry
from modelrailroadops.models.location import Location
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot


class IndustryService:

    @staticmethod
    def _get_or_create_location(
        session,
        name,
    ):

        operating_location = (
            session.execute(
                select(Location).where(
                    Location.name == name
                )
            )
            .scalars()
            .first()
        )

        if operating_location is None:

            operating_location = Location(
                name=name,
                location_type="INDUSTRY",
                active=True,
            )

            session.add(
                operating_location
            )

            session.flush()

        return operating_location
    """
    Handles industry database operations.
    """

    @staticmethod
    def get_all():

        with SessionLocal() as session:

            industries = (
                session.execute(
                    select(Industry)
                    .options(
                        selectinload(
                            Industry.tracks
                        )
                        .selectinload(
                            IndustryTrack.spots
                        )
                        .selectinload(
                            Spot.car
                        )
                    )
                    .order_by(
                        Industry.name
                    )
                )
                .scalars()
                .all()
            )

            #
            # Calculate capacity while the
            # session is still active.
            #

            for industry in industries:

                total_spots = 0
                occupied_spots = 0

                for track in industry.tracks:

                    for spot in track.spots:

                        total_spots += 1

                        if spot.car is not None:
                            occupied_spots += 1

                industry.capacity_total = total_spots

                industry.capacity_occupied = (
                    occupied_spots
                )

                industry.capacity_available = (
                    total_spots
                    - occupied_spots
                )

                if total_spots:

                    industry.capacity_percent = round(
                        occupied_spots
                        / total_spots
                        * 100
                    )

                else:

                    industry.capacity_percent = 0

            return industries

    @staticmethod
    def add(
        name,
        railroad,
        location,
        notes=None,
    ):
        """
        Add a new industry.

        Returns the existing industry if the name
        already exists.
        """

        name = name.strip()

        railroad = railroad.strip()

        location = location.strip()

        if not name:

            return None

        with SessionLocal() as session:

            #
            # Check for an existing industry.
            #

            existing = (
                session.execute(
                    select(Industry)
                    .where(
                        Industry.name == name
                    )
                )
                .scalars()
                .first()
            )

            if existing:

                return existing

            #
            # Create new industry.
            #

            operating_location = (
                IndustryService._get_or_create_location(
                    session,
                    name,
                )
            )

            industry = Industry(
                name=name,
                railroad=railroad,
                location=location,
                notes=notes,
                operating_location_id=operating_location.id,
            )

            session.add(
                industry
            )

            #
            # Flush so SQLAlchemy assigns
            # the database-generated ID.
            #

            session.flush()

            #
            # Commit.
            #

            session.commit()

            #
            # Refresh the object so its database
            # state is current.
            #

            session.refresh(
                industry
            )

            return industry

    @staticmethod
    def update(
        industry_id,
        name,
        railroad,
        location,
        notes=None,
    ):

        name = name.strip()

        railroad = railroad.strip()

        location = location.strip()

        if not name:

            return None

        with SessionLocal() as session:

            industry = session.get(
                Industry,
                industry_id
            )

            if industry is None:

                return None

            #
            # Check whether another industry already
            # uses the requested name.
            #

            duplicate = (
                session.execute(
                    select(Industry)
                    .where(
                        Industry.name == name,
                        Industry.id != industry_id,
                    )
                )
                .scalars()
                .first()
            )

            if duplicate:

                return None

            industry.name = name

            industry.railroad = railroad

            industry.location = location

            industry.notes = notes

            operating_location = (
                IndustryService._get_or_create_location(
                    session,
                    name,
                )
            )

            industry.operating_location_id = (
                operating_location.id
            )

            session.commit()

            session.refresh(
                industry
            )

            return industry

    @staticmethod
    def delete(
        industry_id
    ):

        with SessionLocal() as session:

            industry = session.get(
                Industry,
                industry_id
            )

            if industry is None:

                return False

            session.delete(
                industry
            )

            session.commit()

            return True
