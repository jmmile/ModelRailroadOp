from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.car_movement import CarMovement



class CarLocationService:
    """
    Handles assigning and moving cars between
    industries, tracks, and spots.
    """



    @staticmethod
    def validate_car_for_spot(car, spot):
        """
        Validate whether a car can occupy a spot.
        """

        #
        # Allowed car type
        #

        if spot.allowed_car_type:

            if car.car_type != spot.allowed_car_type:

                return (
                    False,
                    (
                        "Car type not allowed.\n\n"
                        f"Car type: {car.car_type}\n"
                        f"Required: {spot.allowed_car_type}"
                    )
                )



        #
        # Allowed owner
        #

        if spot.allowed_owner:

            if car.owner != spot.allowed_owner:

                return (
                    False,
                    (
                        "Car owner not allowed.\n\n"
                        f"Owner: {car.owner}\n"
                        f"Required: {spot.allowed_owner}"
                    )
                )



        #
        # Maximum length
        #

        if (
            spot.max_length is not None
            and car.length is not None
        ):

            if car.length > spot.max_length:

                return (
                    False,
                    (
                        "Car length exceeds spot limit.\n\n"
                        f"Car length: {car.length} ft\n"
                        f"Maximum: {spot.max_length} ft"
                    )
                )



        #
        # Hazardous restrictions
        #

        if not spot.hazardous_allowed:

            if getattr(
                car,
                "hazardous",
                False
            ):

                return (
                    False,
                    "Hazardous cars are not allowed in this spot."
                )



        #
        # Load only restriction
        #

        if spot.load_only:

            if (
                not car.status
                or car.status.lower() != "loaded"
            ):

                return (
                    False,
                    "This spot requires a loaded car."
                )



        #
        # Empty only restriction
        #

        if spot.empty_only:

            if (
                not car.status
                or car.status.lower() != "empty"
            ):

                return (
                    False,
                    "This spot requires an empty car."
                )



        return True, ""





    @staticmethod
    def assign_car_to_spot(
        car_id,
        spot_id
    ):
        """
        Assign or move a car to a spot.
        """

        with SessionLocal() as session:


            car = session.get(
                Car,
                car_id
            )


            if car is None:

                return False



            spot = session.get(
                Spot,
                spot_id
            )


            if spot is None:

                return False



            #
            # Validate restrictions
            #

            valid, message = (
                CarLocationService.validate_car_for_spot(
                    car,
                    spot
                )
            )


            if not valid:

                return False



            #
            # Check occupancy
            #

            existing_car = (
                session.execute(
                    select(Car)
                    .where(
                        Car.spot_id == spot_id
                    )
                )
                .scalar_one_or_none()
            )


            if (
                existing_car
                and existing_car.id != car_id
            ):

                return False



            track = session.get(
                IndustryTrack,
                spot.track_id
            )


            if track is None:

                return False



            industry = session.get(
                Industry,
                track.industry_id
            )


            if industry is None:

                return False



            #
            # Previous location
            #

            old_location = "Unassigned"



            if car.spot_id:

                old_spot = session.get(
                    Spot,
                    car.spot_id
                )


                old_track = session.get(
                    IndustryTrack,
                    car.track_id
                )


                old_industry = session.get(
                    Industry,
                    car.industry_id
                )


                if (
                    old_spot
                    and old_track
                    and old_industry
                ):

                    old_location = (
                        f"{old_industry.name} - "
                        f"{old_track.name} - "
                        f"Spot {old_spot.spot_number}"
                    )



            #
            # New location
            #

            new_location = (
                f"{industry.name} - "
                f"{track.name} - "
                f"Spot {spot.spot_number}"
            )



            movement_type = (
                "ASSIGN"
                if old_location == "Unassigned"
                else "MOVE"
            )



            #
            # Update car
            #

            car.industry_id = industry.id
            car.track_id = track.id
            car.spot_id = spot.id
            car.location = new_location



            #
            # Add history
            #

            movement = CarMovement(

                car_id=car.id,

                from_location=old_location,

                to_location=new_location,

                movement_type=movement_type,

            )


            session.add(
                movement
            )


            session.commit()


            session.refresh(
                car
            )


            return car





    @staticmethod
    def move_car(
        car_id,
        new_spot_id
    ):

        return CarLocationService.assign_car_to_spot(
            car_id,
            new_spot_id
        )





    @staticmethod
    def clear_car_location(
        car_id
    ):

        with SessionLocal() as session:


            car = session.get(
                Car,
                car_id
            )


            if car is None:

                return False



            old_location = car.location



            car.industry_id = None
            car.track_id = None
            car.spot_id = None
            car.location = "Unassigned"



            movement = CarMovement(

                car_id=car.id,

                from_location=old_location,

                to_location="Unassigned",

                movement_type="REMOVE",

            )


            session.add(
                movement
            )


            session.commit()


            return car





    @staticmethod
    def get_car_location(
        car_id
    ):

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