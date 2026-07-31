from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car


class CarService:
    """Handles all database operations for freight cars."""

    @staticmethod
    def get_all():
        with SessionLocal() as session:
            return (
                session.execute(
                    select(Car).order_by(Car.reporting_mark, Car.number)
                )
                .scalars()
                .all()
            )

    @staticmethod
    def get_by_id(car_id):
        with SessionLocal() as session:
            return session.get(Car, car_id)

    @staticmethod
    def get_by_reporting_mark_and_number(reporting_mark, number):
        with SessionLocal() as session:
            return session.execute(
                select(Car).where(
                    Car.reporting_mark == reporting_mark,
                    Car.number == number,
                )
            ).scalar_one_or_none()

    @staticmethod
    def add(
        reporting_mark,
        number,
        owner="",
        car_type="",
        status="Available",
        location=""
    ):
        with SessionLocal() as session:
            
            existing_car = session.execute(
                select(Car).where(
                    Car.reporting_mark == reporting_mark,
                    Car.number == number
                )
            ).scalar()

            if existing_car:
                return None
                            
                
                        
            
            car = Car(
                reporting_mark=reporting_mark,
                number=number,
                owner=owner,
                car_type=car_type,
                status=status,
                location=location,
            )

            session.add(car)
            session.commit()
            session.refresh(car)


            return car

    @staticmethod
    def update(
        car_id,
        reporting_mark,
        number,
        owner="",
        car_type="",
        status="Available",
        location=""
    ):
        with SessionLocal() as session:
            car = session.get(Car, car_id)

            if car:
                car.reporting_mark = reporting_mark
                car.number = number
                car.owner = owner
                car.car_type = car_type
                car.status = status
                car.location = location

                session.commit()

            return car

    @staticmethod
    def delete(car_id):
        with SessionLocal() as session:
            car = session.get(Car, car_id)

            if car:
                session.delete(car)
                session.commit()