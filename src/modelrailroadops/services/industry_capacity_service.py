from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot



class IndustryService:


    @staticmethod
    def get_all():

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



    @staticmethod
    def get_by_id(
        industry_id
    ):

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
                        )
                        .selectinload(
                            Spot.car
                        )
                    )
                    .where(
                        Industry.id == industry_id
                    )
                )
                .scalars()
                .first()
            )



    @staticmethod
    def add(
        name,
        railroad,
        location,
        notes=None,
    ):

        with SessionLocal() as session:

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



            industry = Industry(

                name=name,

                railroad=railroad,

                location=location,

                notes=notes,

            )


            session.add(
                industry
            )

            session.commit()

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