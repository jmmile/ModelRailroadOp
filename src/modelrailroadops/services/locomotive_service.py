from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.locomotive import Locomotive


class LocomotiveService:
    """
    Handles database operations for locomotives.
    """

    @staticmethod
    def get_all():

        with SessionLocal() as session:

            return (
                session.execute(
                    select(Locomotive)
                    .order_by(
                        Locomotive.reporting_mark,
                        Locomotive.number,
                    )
                )
                .scalars()
                .all()
            )

    @staticmethod
    def get_by_id(
        locomotive_id,
    ):

        with SessionLocal() as session:

            return session.get(
                Locomotive,
                locomotive_id,
            )

    @staticmethod
    def get_by_reporting_mark_and_number(
        reporting_mark,
        number,
    ):

        with SessionLocal() as session:

            return (
                session.execute(
                    select(Locomotive)
                    .where(
                        Locomotive.reporting_mark == reporting_mark,
                        Locomotive.number == number,
                    )
                )
                .scalar_one_or_none()
            )

    @staticmethod
    def add(
        reporting_mark,
        number,
        owner="",
        model="",
        manufacturer="",
        locomotive_type="Diesel",
        horsepower=None,
        dcc_address=None,
        length=None,
        status="AVAILABLE",
        notes="",
    ):

        with SessionLocal() as session:

            existing_locomotive = (
                session.execute(
                    select(Locomotive)
                    .where(
                        Locomotive.reporting_mark == reporting_mark,
                        Locomotive.number == number,
                    )
                )
                .scalar_one_or_none()
            )

            if existing_locomotive:

                return None

            locomotive = Locomotive(
                reporting_mark=reporting_mark,
                number=number,
                owner=owner,
                model=model,
                manufacturer=manufacturer,
                locomotive_type=locomotive_type,
                horsepower=horsepower,
                dcc_address=dcc_address,
                length=length,
                status=status,
                notes=notes,
            )

            session.add(
                locomotive
            )

            session.commit()

            session.refresh(
                locomotive
            )

            return locomotive

    @staticmethod
    def update(
        locomotive_id,
        reporting_mark,
        number,
        owner="",
        model="",
        manufacturer="",
        locomotive_type="Diesel",
        horsepower=None,
        dcc_address=None,
        length=None,
        status="AVAILABLE",
        notes="",
    ):

        with SessionLocal() as session:

            locomotive = session.get(
                Locomotive,
                locomotive_id,
            )

            if locomotive is None:

                return None

            duplicate = (
                session.execute(
                    select(Locomotive)
                    .where(
                        Locomotive.reporting_mark == reporting_mark,
                        Locomotive.number == number,
                        Locomotive.id != locomotive_id,
                    )
                )
                .scalar_one_or_none()
            )

            if duplicate:

                return None

            locomotive.reporting_mark = reporting_mark

            locomotive.number = number

            locomotive.owner = owner

            locomotive.model = model

            locomotive.manufacturer = manufacturer

            locomotive.locomotive_type = locomotive_type

            locomotive.horsepower = horsepower

            locomotive.dcc_address = dcc_address

            locomotive.length = length

            locomotive.status = status

            locomotive.notes = notes

            session.commit()

            session.refresh(
                locomotive
            )

            return locomotive

    @staticmethod
    def delete(
        locomotive_id,
    ):

        with SessionLocal() as session:

            locomotive = session.get(
                Locomotive,
                locomotive_id,
            )

            if locomotive:

                session.delete(
                    locomotive
                )

                session.commit()

                return True

            return False