from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
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
    # OPERATIONS SESSION MOVEMENT STATE
    # ==========================================================

    @staticmethod
    def _prepare_operations_session_for_movement(
        session,
        operations_session_id,
    ):
        """
        Validate an Operations Session before recording a
        car movement against it.

        Car-location movement must never start an Operations
        Session.

        A PLANNED Operations Session becomes ACTIVE through
        the Operations/Switch List workflow when its first
        PICKUP instruction is completed.

        Therefore, a car movement associated with an
        Operations Session is allowed only when that session
        is already ACTIVE.
        """

        if operations_session_id is None:
            return True, ""

        operations_session = session.get(
            OperationsSession,
            operations_session_id,
        )

        if operations_session is None:
            return (
                False,
                "The Operations Session was not found.",
            )

        if operations_session.status == "ACTIVE":
            return True, ""

        if operations_session.status == "PLANNED":
            return (
                False,
                (
                    f"Operations Session '{operations_session.name}' "
                    "is PLANNED and has not started.\n\n"
                    "Complete the first PICKUP instruction to start "
                    "the Operations Session before recording car "
                    "movements against it."
                ),
            )

        return (
            False,
            (
                f"Operations Session '{operations_session.name}' is "
                f"{operations_session.status} and cannot accept car moves."
            ),
        )

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

        if spot is None:
            return (
                False,
                "Spot not found.",
            )

        if car is None:
            return (
                False,
                "Car not found.",
            )

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
                    ),
                )

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
                    ),
                )

        if spot.max_length is not None:

            if car.length is None:

                return (
                    False,
                    (
                        "Car length is unknown.\n\n"
                        f"This spot has a maximum "
                        f"length of "
                        f"{spot.max_length} ft."
                    ),
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
                    ),
                )

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
                    ),
                )

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
                    ),
                )

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
                    ),
                )

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
                    "Car not found.",
                )

            spot = session.get(
                Spot,
                spot_id,
            )

            if spot is None:
                return (
                    False,
                    "Spot not found.",
                )

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
                    "The selected spot is already occupied.",
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
        operations_session_id=None,
        db_session=None,
    ):
        """
        Assign or move a car to a spot.

        operations_session_id is optional. When supplied,
        it is recorded on the resulting CarMovement history
        record.

        A supplied Operations Session must already be ACTIVE.
        Car movement itself never starts an Operations Session.

        When db_session is supplied, the caller owns the
        transaction and is responsible for commit/rollback.

        Returns:

            (True, "")

        when successful.

        Returns:

            (False, "reason")

        when the operation fails.
        """

        owns_session = (
            db_session is None
        )

        session = (
            SessionLocal()
            if owns_session
            else db_session
        )

        try:

            car = session.get(
                Car,
                car_id,
            )

            if car is None:
                return (
                    False,
                    "Car not found.",
                )

            spot = session.get(
                Spot,
                spot_id,
            )

            if spot is None:
                return (
                    False,
                    "Destination spot not found.",
                )

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
                    "The destination spot is already occupied.",
                )

            session_ready, message = (
                CarLocationService._prepare_operations_session_for_movement(
                    session,
                    operations_session_id,
                )
            )

            if not session_ready:
                return (
                    False,
                    message,
                )

            track = session.get(
                IndustryTrack,
                spot.track_id,
            )

            if track is None:
                return (
                    False,
                    "The spot's industry track could not be found.",
                )

            industry = session.get(
                Industry,
                track.industry_id,
            )

            if industry is None:
                return (
                    False,
                    "The spot's industry could not be found.",
                )

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

            new_location = (
                f"{industry.name} - "
                f"{track.name} - "
                f"Spot "
                f"{spot.spot_number}"
            )

            movement_type = (
                "ASSIGN"
                if old_location == "Unassigned"
                else "MOVE"
            )

            car.industry_id = industry.id
            car.track_id = track.id
            car.spot_id = spot.id
            car.operating_location_id = (
                industry.operating_location_id
            )
            car.operating_track_id = (
                track.operating_track_id
            )
            car.location = new_location

            movement = CarMovement(
                car_id=car.id,
                operations_session_id=operations_session_id,
                from_location=old_location,
                to_location=new_location,
                movement_type=movement_type,
            )

            session.add(
                movement
            )

            if owns_session:

                session.commit()

                session.refresh(
                    car
                )

            return (
                True,
                "",
            )

        except Exception as exc:

            if owns_session:
                session.rollback()

            return (
                False,
                str(exc),
            )

        finally:

            if owns_session:
                session.close()

    # ==========================================================
    # MOVE CAR TO GENERAL LOCATION TRACK
    # ==========================================================

    @staticmethod
    def move_car_to_location_track_with_message(
        car_id,
        location_track_id,
        operations_session_id=None,
        db_session=None,
    ):
        """
        Move a car to a yard, staging, or interchange track.

        When operations_session_id is supplied, the Operations
        Session must already be ACTIVE. Car movement itself
        never starts an Operations Session.

        When db_session is supplied, the caller owns the
        transaction and is responsible for commit/rollback.
        """

        owns_session = (
            db_session is None
        )

        session = (
            SessionLocal()
            if owns_session
            else db_session
        )

        try:

            car = session.get(
                Car,
                car_id,
            )

            track = session.get(
                LocationTrack,
                location_track_id,
            )

            if car is None:
                return (
                    False,
                    "Car not found.",
                )

            if track is None:
                return (
                    False,
                    "Destination track not found.",
                )

            location = session.get(
                Location,
                track.location_id,
            )

            if location is None:
                return (
                    False,
                    "Destination location not found.",
                )

            if (
                not location.active
                or not track.active
            ):
                return (
                    False,
                    "Destination location and track must be active.",
                )

            industry_track = (
                session.execute(
                    select(
                        IndustryTrack
                    ).where(
                        IndustryTrack.operating_track_id
                        == location_track_id
                    )
                )
                .scalars()
                .first()
            )

            if industry_track is not None:
                return (
                    False,
                    "Industry tracks require an available destination spot.",
                )

            if track.capacity is not None:

                occupied = len(
                    session.execute(
                        select(Car).where(
                            Car.operating_track_id
                            == location_track_id,
                            Car.id
                            != car_id,
                        )
                    )
                    .scalars()
                    .all()
                )

                if occupied >= track.capacity:
                    return (
                        False,
                        "The destination track is at capacity.",
                    )

            session_ready, message = (
                CarLocationService._prepare_operations_session_for_movement(
                    session,
                    operations_session_id,
                )
            )

            if not session_ready:
                return (
                    False,
                    message,
                )

            old_location = (
                car.location
                or "Unassigned"
            )

            new_location = (
                f"{location.name} - "
                f"{track.name}"
            )

            movement_type = (
                "ASSIGN"
                if old_location == "Unassigned"
                else "MOVE"
            )

            car.industry_id = None
            car.track_id = None
            car.spot_id = None
            car.operating_location_id = (
                location.id
            )
            car.operating_track_id = (
                track.id
            )
            car.location = new_location

            session.add(
                CarMovement(
                    car_id=car.id,
                    operations_session_id=operations_session_id,
                    from_location=old_location,
                    to_location=new_location,
                    movement_type=movement_type,
                )
            )

            if owns_session:

                session.commit()

                session.refresh(
                    car
                )

            return (
                True,
                "",
            )

        except Exception as exc:

            if owns_session:
                session.rollback()

            return (
                False,
                str(exc),
            )

        finally:

            if owns_session:
                session.close()

    # ==========================================================
    # ASSIGN CAR
    # ==========================================================

    @staticmethod
    def assign_car_to_spot(
        car_id,
        spot_id,
        operations_session_id=None,
    ):
        """
        Assign or move a car to a spot.

        This method is retained for compatibility with
        existing parts of the application.

        operations_session_id is optional and is passed
        through to the movement-history record.

        Returns the Car object on success or False
        on failure.
        """

        success, message = (
            CarLocationService.assign_car_to_spot_with_message(
                car_id,
                spot_id,
                operations_session_id,
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
        operations_session_id=None,
    ):
        """
        Move a car to a new spot.

        operations_session_id is optional. When supplied,
        it is recorded with the resulting CarMovement.

        Returns the Car object on success or False
        on failure.
        """

        success, message = (
            CarLocationService.assign_car_to_spot_with_message(
                car_id,
                new_spot_id,
                operations_session_id,
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
        operations_session_id=None,
    ):
        """
        Move a car to a new spot and return a useful
        success/failure message.

        operations_session_id is optional and is recorded
        with the movement when supplied.
        """

        return (
            CarLocationService.assign_car_to_spot_with_message(
                car_id,
                new_spot_id,
                operations_session_id,
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

            old_location = (
                car.location
                or "Unassigned"
            )

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

            car.industry_id = None
            car.track_id = None
            car.spot_id = None
            car.operating_location_id = None
            car.operating_track_id = None
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
            location_name = None
            location_type = None
            traffic_use = None

            if car.industry_id is not None:

                industry = session.get(
                    Industry,
                    car.industry_id,
                )

                if industry is not None:
                    industry_name = (
                        industry.name
                    )

            if car.track_id is not None:

                track = session.get(
                    IndustryTrack,
                    car.track_id,
                )

                if track is not None:
                    track_name = (
                        track.name
                    )

            if car.operating_location_id is not None:

                operating_location = session.get(
                    Location,
                    car.operating_location_id,
                )

                if operating_location is not None:
                    location_name = (
                        operating_location.name
                    )
                    location_type = (
                        operating_location.location_type
                    )

            if car.operating_track_id is not None:

                operating_track = session.get(
                    LocationTrack,
                    car.operating_track_id,
                )

                if operating_track is not None:
                    track_name = (
                        operating_track.name
                    )
                    traffic_use = (
                        operating_track.traffic_use
                    )

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
                "operating_location": location_name,
                "location_type": location_type,
                "track": track_name,
                "spot": spot_number,
                "traffic_use": traffic_use,
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
        car_id,
    ):

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id,
            )

            if car:

                session.delete(
                    car
                )

                session.commit()