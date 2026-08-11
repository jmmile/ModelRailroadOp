
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

    This service is the central authority for:

        - Spot restriction validation
        - Car assignment
        - Car movement
        - Removing cars from locations
        - Determining eligible cars
        - Recording movement history
    """

    # ==========================================================
    # TEXT NORMALIZATION
    # ==========================================================

    @staticmethod
    def normalize_text(value):
        """
        Normalize text for restriction comparisons.

        Leading/trailing whitespace is removed and
        comparisons are made case-insensitively.
        """

        if value is None:
            return ""

        return str(value).strip().casefold()

    # ==========================================================
    # SPOT VALIDATION
    # ==========================================================

    @staticmethod
    def validate_car_for_spot(
        car,
        spot,
    ):
        """
        Validate whether a car can occupy a spot.

        Returns:

            (True, "")

        when the car is allowed.

        Returns:

            (False, "reason")

        when the car violates a restriction.
        """

        #
        # Spot
        #

        if spot is None:

            return (
                False,
                "Spot not found."
            )

        #
        # Car
        #

        if car is None:

            return (
                False,
                "Car not found."
            )

        #
        # Allowed car type
        #
        # Compare case-insensitively and ignore
        # accidental leading/trailing spaces.
        #

        if spot.allowed_car_type:

            car_type = (
                CarLocationService.normalize_text(
                    car.car_type
                )
            )

            allowed_car_type = (
                CarLocationService.normalize_text(
                    spot.allowed_car_type
                )
            )

            if car_type != allowed_car_type:

                return (
                    False,
                    (
                        "Car type not allowed.\n\n"
                        f"Car type: "
                        f"{car.car_type or 'Unknown'}\n"
                        f"Required: "
                        f"{spot.allowed_car_type}"
                    )
                )

        #
        # Allowed owner
        #
        # Compare case-insensitively and ignore
        # accidental leading/trailing spaces.
        #

        if spot.allowed_owner:

            car_owner = (
                CarLocationService.normalize_text(
                    car.owner
                )
            )

            allowed_owner = (
                CarLocationService.normalize_text(
                    spot.allowed_owner
                )
            )

            if car_owner != allowed_owner:

                return (
                    False,
                    (
                        "Car owner not allowed.\n\n"
                        f"Owner: "
                        f"{car.owner or 'Unknown'}\n"
                        f"Required: "
                        f"{spot.allowed_owner}"
                    )
                )

        #
        # Maximum length
        #

        if spot.max_length is not None:

            if car.length is None:

                return (
                    False,
                    (
                        "Car length is unknown.\n\n"
                        f"This spot has a maximum "
                        f"length of "
                        f"{spot.max_length} ft."
                    )
                )

            if car.length > spot.max_length:

                return (
                    False,
                    (
                        "Car length exceeds spot limit.\n\n"
                        f"Car length: "
                        f"{car.length} ft\n"
                        f"Maximum: "
                        f"{spot.max_length} ft"
                    )
                )

        #
        # Hazardous restriction
        #

        if not spot.hazardous_allowed:

            if getattr(
                car,
                "hazardous",
                False,
            ):

                return (
                    False,
                    (
                        "Hazardous cars are not "
                        "allowed in this spot."
                    )
                )

        #
        # Loaded-only restriction
        #

        if spot.load_only:

            car_status = (
                CarLocationService.normalize_text(
                    car.status
                )
            )

            if car_status != "loaded":

                return (
                    False,
                    (
                        "This spot requires "
                        "a loaded car.\n\n"
                        f"Car status: "
                        f"{car.status or 'Unknown'}"
                    )
                )

        #
        # Empty-only restriction
        #

        if spot.empty_only:

            car_status = (
                CarLocationService.normalize_text(
                    car.status
                )
            )

            if car_status != "empty":

                return (
                    False,
                    (
                        "This spot requires "
                        "an empty car.\n\n"
                        f"Car status: "
                        f"{car.status or 'Unknown'}"
                    )
                )

        #
        # All restrictions passed.
        #

        return True, ""

    # ==========================================================
    # CHECK WHETHER CAR CAN BE ASSIGNED
    # ==========================================================

    @staticmethod
    def can_assign_car_to_spot(
        car_id,
        spot_id,
    ):
        """
        Determine whether a car can be assigned to a spot.

        This performs the complete validation without
        changing the database.

        Returns:

            (True, "")

        or:

            (False, "reason")
        """

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id,
            )

            if car is None:

                return (
                    False,
                    "Car not found."
                )

            spot = session.get(
                Spot,
                spot_id,
            )

            if spot is None:

                return (
                    False,
                    "Spot not found."
                )

            #
            # Validate spot restrictions.
            #

            valid, message = (
                CarLocationService.validate_car_for_spot(
                    car,
                    spot,
                )
            )

            if not valid:

                return (
                    False,
                    message,
                )

            #
            # Check whether another car occupies
            # the destination spot.
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
                existing_car is not None
                and existing_car.id != car.id
            ):

                return (
                    False,
                    "The selected spot is already occupied."
                )

            return True, ""

    # ==========================================================
    # GET ELIGIBLE UNASSIGNED CARS
    # ==========================================================

    @staticmethod
    def get_eligible_cars_for_spot(
        spot_id,
    ):
        """
        Return all unassigned cars that can legally
        occupy the specified spot.

        Cars that fail any spot restriction are excluded.

        Returns a list of Car objects.
        """

        with SessionLocal() as session:

            spot = session.get(
                Spot,
                spot_id,
            )

            if spot is None:

                return []

            #
            # Only completely unassigned cars are candidates.
            #

            cars = (
                session.execute(
                    select(Car)
                    .where(
                        Car.industry_id.is_(None),
                        Car.track_id.is_(None),
                        Car.spot_id.is_(None),
                    )
                    .order_by(
                        Car.reporting_mark,
                        Car.number,
                    )
                )
                .scalars()
                .all()
            )

            eligible_cars = []

            for car in cars:

                valid, _ = (
                    CarLocationService.validate_car_for_spot(
                        car,
                        spot,
                    )
                )

                if valid:

                    eligible_cars.append(
                        car
                    )

            return eligible_cars

    # ==========================================================
    # ASSIGN CAR WITH MESSAGE
    # ==========================================================

    @staticmethod
    def assign_car_to_spot_with_message(
        car_id,
        spot_id,
    ):
        """
        Assign or move a car to a spot.

        Returns:

            (True, "")

        when successful.

        Returns:

            (False, "reason")

        when the operation fails.
        """

        with SessionLocal() as session:

            #
            # Get car.
            #

            car = session.get(
                Car,
                car_id,
            )

            if car is None:

                return (
                    False,
                    "Car not found."
                )

            #
            # Get destination spot.
            #

            spot = session.get(
                Spot,
                spot_id,
            )

            if spot is None:

                return (
                    False,
                    "Destination spot not found."
                )

            #
            # Validate spot restrictions.
            #

            valid, message = (
                CarLocationService.validate_car_for_spot(
                    car,
                    spot,
                )
            )

            if not valid:

                return (
                    False,
                    message,
                )

            #
            # Check destination occupancy.
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
                existing_car is not None
                and existing_car.id != car.id
            ):

                return (
                    False,
                    "The destination spot is already occupied."
                )

            #
            # Get track.
            #

            track = session.get(
                IndustryTrack,
                spot.track_id,
            )

            if track is None:

                return (
                    False,
                    "The spot's industry track could not be found."
                )

            #
            # Get industry.
            #

            industry = session.get(
                Industry,
                track.industry_id,
            )

            if industry is None:

                return (
                    False,
                    "The spot's industry could not be found."
                )

            #
            # Determine previous location.
            #

            old_location = "Unassigned"

            if car.spot_id is not None:

                old_spot = session.get(
                    Spot,
                    car.spot_id,
                )

                old_track = None

                if car.track_id is not None:

                    old_track = session.get(
                        IndustryTrack,
                        car.track_id,
                    )

                old_industry = None

                if car.industry_id is not None:

                    old_industry = session.get(
                        Industry,
                        car.industry_id,
                    )

                if (
                    old_spot is not None
                    and old_track is not None
                    and old_industry is not None
                ):

                    old_location = (
                        f"{old_industry.name} - "
                        f"{old_track.name} - "
                        f"Spot "
                        f"{old_spot.spot_number}"
                    )

            #
            # Handle a car that has an industry/track
            # location but no spot.
            #

            elif (
                car.track_id is not None
                or car.industry_id is not None
            ):

                old_track = None

                if car.track_id is not None:

                    old_track = session.get(
                        IndustryTrack,
                        car.track_id,
                    )

                old_industry = None

                if car.industry_id is not None:

                    old_industry = session.get(
                        Industry,
                        car.industry_id,
                    )

                if (
                    old_industry is not None
                    and old_track is not None
                ):

                    old_location = (
                        f"{old_industry.name} - "
                        f"{old_track.name}"
                    )

                elif old_industry is not None:

                    old_location = (
                        old_industry.name
                    )

            #
            # New location.
            #

            new_location = (
                f"{industry.name} - "
                f"{track.name} - "
                f"Spot "
                f"{spot.spot_number}"
            )

            #
            # Determine movement type.
            #

            movement_type = (
                "ASSIGN"
                if old_location == "Unassigned"
                else "MOVE"
            )

            #
            # Update car location.
            #

            car.industry_id = industry.id
            car.track_id = track.id
            car.spot_id = spot.id
            car.location = new_location

            #
            # Record movement history.
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

            #
            # Commit transaction.
            #

            session.commit()

            session.refresh(
                car
            )

            return (
                True,
                ""
            )

    # ==========================================================
    # ASSIGN CAR
    # ==========================================================

    @staticmethod
    def assign_car_to_spot(
        car_id,
        spot_id,
    ):
        """
        Assign or move a car to a spot.

        This method is retained for compatibility with
        existing parts of the application.

        Returns the Car object on success or False
        on failure.
        """

        success, message = (
            CarLocationService.assign_car_to_spot_with_message(
                car_id,
                spot_id,
            )
        )

        if not success:

            return False

        with SessionLocal() as session:

            return session.get(
                Car,
                car_id,
            )

    # ==========================================================
    # MOVE CAR
    # ==========================================================

    @staticmethod
    def move_car(
        car_id,
        new_spot_id,
    ):
        """
        Move a car to a new spot.

        Returns the Car object on success or False
        on failure.
        """

        success, message = (
            CarLocationService.assign_car_to_spot_with_message(
                car_id,
                new_spot_id,
            )
        )

        if not success:

            return False

        with SessionLocal() as session:

            return session.get(
                Car,
                car_id,
            )

    # ==========================================================
    # MOVE CAR WITH MESSAGE
    # ==========================================================

    @staticmethod
    def move_car_with_message(
        car_id,
        new_spot_id,
    ):
        """
        Move a car to a new spot and return a useful
        success/failure message.
        """

        return (
            CarLocationService.assign_car_to_spot_with_message(
                car_id,
                new_spot_id,
            )
        )

    # ==========================================================
    # CLEAR CAR LOCATION
    # ==========================================================

    @staticmethod
    def clear_car_location(
        car_id,
    ):
        """
        Remove a car from its current industry,
        track, and spot.

        The car remains in the roster and becomes
        unassigned.

        A movement-history record is created.

        Returns the Car object on success or False
        if the car does not exist.
        """

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id,
            )

            if car is None:

                return False

            #
            # Previous location.
            #

            old_location = (
                car.location
                or "Unassigned"
            )

            #
            # If location text is missing, reconstruct
            # the location from the relationships.
            #

            if old_location == "Unassigned":

                if (
                    car.spot_id is not None
                    and car.track_id is not None
                    and car.industry_id is not None
                ):

                    old_spot = session.get(
                        Spot,
                        car.spot_id,
                    )

                    old_track = session.get(
                        IndustryTrack,
                        car.track_id,
                    )

                    old_industry = session.get(
                        Industry,
                        car.industry_id,
                    )

                    if (
                        old_spot is not None
                        and old_track is not None
                        and old_industry is not None
                    ):

                        old_location = (
                            f"{old_industry.name} - "
                            f"{old_track.name} - "
                            f"Spot "
                            f"{old_spot.spot_number}"
                        )

            #
            # Clear location.
            #

            car.industry_id = None
            car.track_id = None
            car.spot_id = None
            car.location = "Unassigned"

            #
            # Record movement.
            #

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

            session.refresh(
                car
            )

            return car

    # ==========================================================
    # GET CAR LOCATION
    # ==========================================================

    @staticmethod
    def get_car_location(
        car_id,
    ):
        """
        Return the current structured location
        of a car.
        """

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id,
            )

            if car is None:

                return None

            industry_name = None
            track_name = None
            spot_number = None

            #
            # Load industry.
            #

            if car.industry_id is not None:

                industry = session.get(
                    Industry,
                    car.industry_id,
                )

                if industry is not None:

                    industry_name = (
                        industry.name
                    )

            #
            # Load track.
            #

            if car.track_id is not None:

                track = session.get(
                    IndustryTrack,
                    car.track_id,
                )

                if track is not None:

                    track_name = (
                        track.name
                    )

            #
            # Load spot.
            #

            if car.spot_id is not None:

                spot = session.get(
                    Spot,
                    car.spot_id,
                )

                if spot is not None:

                    spot_number = (
                        spot.spot_number
                    )

            return {
                "car": (
                    f"{car.reporting_mark} "
                    f"{car.number}"
                ),

                "industry": industry_name,

                "track": track_name,

                "spot": spot_number,

                "location": (
                    car.location
                    or "Unassigned"
                ),
            }

    # ==========================================================
    # DELETE CAR
    # ==========================================================

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
