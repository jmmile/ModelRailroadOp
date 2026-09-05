from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.passenger_car import PassengerCar


class PassengerCarService:
    """
    Handles database operations for passenger equipment.
    """

    @staticmethod
    def get_all():

        with SessionLocal() as session:

            return (
                session.execute(
                    select(PassengerCar)
                    .order_by(
                        PassengerCar.reporting_mark,
                        PassengerCar.number,
                    )
                )
                .scalars()
                .all()
            )

    @staticmethod
    def get_by_id(
        passenger_car_id,
    ):

        with SessionLocal() as session:

            return session.get(
                PassengerCar,
                passenger_car_id,
            )

    @staticmethod
    def get_by_reporting_mark_and_number(
        reporting_mark,
        number,
    ):

        with SessionLocal() as session:

            return (
                session.execute(
                    select(PassengerCar)
                    .where(
                        PassengerCar.reporting_mark == reporting_mark,
                        PassengerCar.number == number,
                    )
                )
                .scalar_one_or_none()
            )

    @staticmethod
    def add(
        reporting_mark,
        number,
        name="",
        owner="",
        equipment_type="Coach",
        length=None,
        status="AVAILABLE",
        notes="",
    ):

        with SessionLocal() as session:

            existing_passenger_car = (
                session.execute(
                    select(PassengerCar)
                    .where(
                        PassengerCar.reporting_mark == reporting_mark,
                        PassengerCar.number == number,
                    )
                )
                .scalar_one_or_none()
            )

            if existing_passenger_car:

                return None

            passenger_car = PassengerCar(
                reporting_mark=reporting_mark,
                number=number,
                name=name,
                owner=owner,
                equipment_type=equipment_type,
                length=length,
                status=status,
                notes=notes,
            )

            session.add(
                passenger_car
            )

            session.commit()

            session.refresh(
                passenger_car
            )

            return passenger_car

    @staticmethod
    def update(
        passenger_car_id,
        reporting_mark,
        number,
        name="",
        owner="",
        equipment_type="Coach",
        length=None,
        status="AVAILABLE",
        notes="",
    ):

        with SessionLocal() as session:

            passenger_car = session.get(
                PassengerCar,
                passenger_car_id,
            )

            if passenger_car is None:

                return None

            duplicate = (
                session.execute(
                    select(PassengerCar)
                    .where(
                        PassengerCar.reporting_mark == reporting_mark,
                        PassengerCar.number == number,
                        PassengerCar.id != passenger_car_id,
                    )
                )
                .scalar_one_or_none()
            )

            if duplicate:

                return None

            passenger_car.reporting_mark = reporting_mark
            passenger_car.number = number
            passenger_car.name = name
            passenger_car.owner = owner
            passenger_car.equipment_type = equipment_type
            passenger_car.length = length
            passenger_car.status = status
            passenger_car.notes = notes

            session.commit()

            session.refresh(
                passenger_car
            )

            return passenger_car

    @staticmethod
    def delete(
        passenger_car_id,
    ):

        with SessionLocal() as session:

            passenger_car = session.get(
                PassengerCar,
                passenger_car_id,
            )

            if passenger_car:

                session.delete(
                    passenger_car
                )

                session.commit()

                return True

            return False