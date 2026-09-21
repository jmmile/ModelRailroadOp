from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.passenger_car import PassengerCar
from modelrailroadops.services import passenger_image_service as images


class PassengerCarService:
    """
    Handles database operations for passenger equipment.
    """

    @staticmethod
    def _check_image_owner(session, identity, passenger_car_id=None):
        key = images.image_key(*identity)
        for other in session.scalars(select(PassengerCar)):
            if other.id != passenger_car_id and images.image_key(
                other.reporting_mark, other.number
            ) == key:
                raise ValueError(
                    "Another passenger car has the same picture identity (ignoring case). "
                    "Use a distinct reporting mark and number."
                )

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
        picture=None,
        remove_picture=False,
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

            PassengerCarService._check_image_owner(session, (reporting_mark, number))

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

            session.flush()
            with images.picture_change(
                None, (reporting_mark, number), picture, remove_picture
            ):
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
        picture=None,
        remove_picture=False,
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

            old_identity = (passenger_car.reporting_mark, passenger_car.number)
            if images.find_image(*old_identity):
                PassengerCarService._check_image_owner(session, old_identity, passenger_car_id)
            PassengerCarService._check_image_owner(
                session, (reporting_mark, number), passenger_car_id
            )

            passenger_car.reporting_mark = reporting_mark
            passenger_car.number = number
            passenger_car.name = name
            passenger_car.owner = owner
            passenger_car.equipment_type = equipment_type
            passenger_car.length = length
            passenger_car.status = status
            passenger_car.notes = notes

            session.flush()
            with images.picture_change(
                old_identity, (reporting_mark, number), picture, remove_picture
            ):
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
