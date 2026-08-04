from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot


class CarLocationService:
    """
    Handles assigning and moving cars between
    industries, tracks, and spots.
    """


    @staticmethod
    def assign_car_to_spot(car_id, spot_id):
        """
        Assign a car to a spot.
        If the car already has a location,
        it is moved automatically.
        """

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id
            )

            if car is None:
                return None


            spot = session.get(
                Spot,
                spot_id
            )

            if spot is None:
                return None


            # Check destination spot
            existing_car = session.execute(
                select(Car)
                .where(
                    Car.spot_id == spot_id
                )
            ).scalar_one_or_none()


            if existing_car and existing_car.id != car_id:
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


            #
            # Clear previous location
            #
            car.industry_id = None
            car.track_id = None
            car.spot_id = None


            #
            # Assign new location
            #
            car.industry_id = industry.id
            car.track_id = track.id
            car.spot_id = spot.id


            car.location = (
                f"{industry.name} - "
                f"{track.name} - "
                f"Spot {spot.spot_number}"
            )


            session.commit()
            session.refresh(car)

            return car



    @staticmethod
    def move_car(car_id, new_spot_id):
        """
        Move an existing car to another spot.
        """

        return CarLocationService.assign_car_to_spot(
            car_id,
            new_spot_id
        )



    @staticmethod
    def clear_car_location(car_id):
        """
        Remove a car from an industry spot.
        """

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id
            )

            if car is None:
                return None


            car.industry_id = None
            car.track_id = None
            car.spot_id = None


            car.location = "Unassigned"


            session.commit()
            session.refresh(car)

            return car



    @staticmethod
    def get_car_location(car_id):
        """
        Return the current operational location
        of a car.
        """

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id
            )

            if car is None:
                return None


            return {
                "car": (
                    f"{car.reporting_mark} "
                    f"{car.number}"
                ),

                "industry": (
                    car.industry.name
                    if car.industry
                    else None
                ),

                "track": (
                    car.track.name
                    if car.track
                    else None
                ),

                "spot": (
                    car.spot.spot_number
                    if car.spot
                    else None
                ),
            }