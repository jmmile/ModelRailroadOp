
from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot


class CarService:
    """Handles all database operations for freight cars."""


    @staticmethod
    def get_all():

        with SessionLocal() as session:

            return (
                session.execute(
                    select(Car)
                    .order_by(
                        Car.reporting_mark,
                        Car.number
                    )
                )
                .scalars()
                .all()
            )



    @staticmethod
    def get_by_id(
        car_id
    ):

        with SessionLocal() as session:

            return session.get(
                Car,
                car_id
            )



    @staticmethod
    def get_by_reporting_mark_and_number(
        reporting_mark,
        number
    ):

        with SessionLocal() as session:

            return session.execute(
                select(Car)
                .where(
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
        length=None,
        status="Available",
        location=""
    ):

        with SessionLocal() as session:

            existing_car = session.execute(
                select(Car)
                .where(
                    Car.reporting_mark == reporting_mark,
                    Car.number == number
                )
            ).scalar_one_or_none()


            if existing_car:

                return None


            car = Car(
                reporting_mark=reporting_mark,
                number=number,
                owner=owner,
                car_type=car_type,
                length=length,
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
        length=None,
        status="Available",
        location=""
    ):

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id
            )


            if car:

                car.reporting_mark = reporting_mark

                car.number = number

                car.owner = owner

                car.car_type = car_type

                car.length = length

                car.status = status

                car.location = location


                session.commit()

                session.refresh(car)


            return car



    @staticmethod
    def assign_to_spot(
        car_id,
        spot_id
    ):
        """
        Assign a freight car to a specific spot.

        The track and industry are automatically determined
        from the selected spot.

        Returns:
            Car object on success.

        Raises:
            ValueError if the car, spot, or parent track/industry
            cannot be found, or if the spot is already occupied.
        """

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id
            )


            if car is None:

                raise ValueError(
                    "Car not found."
                )


            spot = session.get(
                Spot,
                spot_id
            )


            if spot is None:

                raise ValueError(
                    "Spot not found."
                )


            track = session.get(
                IndustryTrack,
                spot.track_id
            )


            if track is None:

                raise ValueError(
                    "The selected spot does not have a valid track."
                )


            industry = session.get(
                Industry,
                track.industry_id
            )


            if industry is None:

                raise ValueError(
                    "The selected track does not have a valid industry."
                )


            occupied_car = session.execute(
                select(Car)
                .where(
                    Car.spot_id == spot_id,
                    Car.id != car_id,
                )
            ).scalar_one_or_none()


            if occupied_car:

                raise ValueError(
                    "The selected spot is already occupied."
                )


            car.industry_id = industry.id

            car.track_id = track.id

            car.spot_id = spot.id


            #
            # Keep the existing location field synchronized
            # while the application transitions to the new
            # Industry -> Track -> Spot location system.
            #

            car.location = (
                f"{industry.name} - "
                f"{track.name} - "
                f"Spot {spot.spot_number}"
            )


            session.commit()

            session.refresh(car)


            return car



    @staticmethod
    def clear_spot_assignment(
        car_id
    ):
        """
        Remove the Industry / Track / Spot assignment
        from a freight car.

        The existing location text is changed to
        'Unassigned' while the old location system
        remains in the application.
        """

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id
            )


            if car is None:

                raise ValueError(
                    "Car not found."
                )


            car.industry_id = None

            car.track_id = None

            car.spot_id = None

            car.location = "Unassigned"


            session.commit()

            session.refresh(car)


            return car



    @staticmethod
    def get_location(
        car_id
    ):
        """
        Return the complete operating location for a car.

        Returns:
            Dictionary containing the Industry, Track, and Spot,
            or None if the car has no spot assignment.
        """

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id
            )


            if car is None:

                return None


            if car.spot_id is None:

                return None


            spot = session.get(
                Spot,
                car.spot_id
            )


            if spot is None:

                return None


            track = session.get(
                IndustryTrack,
                spot.track_id
            )


            if track is None:

                return None


            industry = session.get(
                Industry,
                track.industry_id
            )


            if industry is None:

                return None


            return {
                "industry": industry,
                "track": track,
                "spot": spot,
            }



    @staticmethod
    def delete(
        car_id
    ):

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id
            )


            if car:

                session.delete(car)

                session.commit()