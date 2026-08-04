from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack


class IndustryService:
    """
    Service methods for managing industries.
    """


    @staticmethod
    def add(
        name,
        railroad,
        location,
        notes=None,
    ):
        """
        Add a new industry.
        """

        with SessionLocal() as session:

            existing = session.execute(
                select(Industry).where(
                    Industry.name == name
                )
            ).scalar_one_or_none()


            if existing:
                return existing


            industry = Industry(
                name=name,
                railroad=railroad,
                location=location,
                notes=notes,
            )


            session.add(industry)

            session.commit()

            session.refresh(industry)

            return industry



    @staticmethod
    def update(
        industry_id,
        name,
        railroad,
        location,
        notes=None,
    ):
        """
        Update an existing industry.
        """

        with SessionLocal() as session:

            industry = session.get(
                Industry,
                industry_id
            )


            if industry is None:
                return None


            industry.name = name
            industry.railroad = railroad
            industry.location = location
            industry.notes = notes


            session.commit()

            session.refresh(industry)

            return industry



    @staticmethod
    def get_all():
        """
        Return all industries with
        tracks, spots, and cars loaded.
        """

        with SessionLocal() as session:

            return (
                session.execute(
                    select(Industry)
                    .options(
                        selectinload(
                            Industry.tracks
                        )
                        .selectinload(
                            IndustryTrack.spots
                        ),

                        selectinload(
                            Industry.tracks
                        )
                        .selectinload(
                            IndustryTrack.cars
                        ),

                        selectinload(
                            Industry.cars
                        ),
                    )
                    .order_by(
                        Industry.name
                    )
                )
                .scalars()
                .unique()
                .all()
            )



    @staticmethod
    def get_by_id(
        industry_id
    ):
        """
        Return an industry with
        related data loaded.
        """

        with SessionLocal() as session:

            return (
                session.execute(
                    select(Industry)
                    .options(
                        selectinload(
                            Industry.tracks
                        )
                        .selectinload(
                            IndustryTrack.spots
                        ),

                        selectinload(
                            Industry.tracks
                        )
                        .selectinload(
                            IndustryTrack.cars
                        ),

                        selectinload(
                            Industry.cars
                        ),
                    )
                    .where(
                        Industry.id == industry_id
                    )
                )
                .scalars()
                .unique()
                .one_or_none()
            )



    @staticmethod
    def delete(
        industry_id
    ):
        """
        Delete an industry.
        """

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