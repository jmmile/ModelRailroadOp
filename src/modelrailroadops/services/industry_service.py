from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.industry import Industry


class IndustryService:

    @staticmethod
    def get_all():
        with SessionLocal() as session:
            return (
                session.execute(
                    select(Industry)
                    .options(selectinload(Industry.tracks))
                    .order_by(Industry.name)
                )
                .scalars()
                .all()
            )

    @staticmethod
    def add(
        name,
        railroad="",
        location="",
        #track="",
        #spots=1,
        notes=""
    ):
        with SessionLocal() as session:

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
        railroad="",
        location="",
        notes=""
    ):

        with SessionLocal() as session:

            industry = session.get(Industry, industry_id)

            if industry:
                industry.name = name
                industry.railroad = railroad
                industry.location = location
                industry.notes = notes

                session.commit()

            return industry

    @staticmethod
    def delete(industry_id):

        with SessionLocal() as session:

            industry = session.get(Industry, industry_id)

            if industry:
                session.delete(industry)
                session.commit()