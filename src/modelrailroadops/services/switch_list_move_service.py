from datetime import datetime

from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.car_location_service import (
    CarLocationService,
)


class SwitchListMoveService:
    """
    Service for validating and completing switch-list moves.

    This service is responsible for moving a car from its
    current location to the destination specified by its
    Waybill.

    It validates destination spot restrictions before
    changing the database.
    """

    # ==========================================================
    # VALIDATE OPERATIONS SESSION
    # ==========================================================

    @staticmethod
    def validate_active_operations_session(waybill, session):
        """Allow a planned session to start with its first physical move."""

        operations_session_id = getattr(
            waybill,
            "operations_session_id",
            None,
        )

        if operations_session_id is None:
            return "This Waybill is not assigned to an Operations Session."

        operations_session = session.get(
            OperationsSession,
            operations_session_id,
        )

        if operations_session is None:
            return "The Waybill's Operations Session was not found."

        if operations_session.status not in ("PLANNED", "ACTIVE"):
            return (
                f"Operations Session '{operations_session.name}' is "
                f"{operations_session.status} and cannot accept car moves."
            )

        return None

    # ==========================================================
    # VALIDATE SPOT
    # ==========================================================

    @staticmethod
    def validate_general_destination(car, waybill, session):
        track_id = getattr(waybill, "destination_location_track_id", None)
        location_id = getattr(waybill, "destination_location_id", None)

        if location_id is None or track_id is None:
            return "This Waybill does not have a complete destination."

        location = session.get(Location, location_id)
        track = session.get(LocationTrack, track_id)

        if location is None or track is None or track.location_id != location.id:
            return "The destination Location or Track was not found."
        if not location.active or not track.active:
            return "The destination Location and Track must be active."

        if track.capacity is not None:
            occupied = len(
                session.execute(
                    select(Car).where(
                        Car.operating_track_id == track.id,
                        Car.id != car.id,
                    )
                ).scalars().all()
            )
            if occupied >= track.capacity:
                return "The destination track is at capacity."

        return None

    @staticmethod
    def validate_spot(
        car,
        spot,
    ):
        """
        Validate whether a car may occupy a destination spot.

        Returns:

            None
                The car is allowed.

            str
                An explanation of why the car is not allowed.
        """

        if car is None:

            return "Car was not found."

        if spot is None:

            return "Destination spot was not found."

        valid, message = (
            CarLocationService.validate_car_for_spot(
                car,
                spot,
            )
        )

        if not valid:

            return message

        return None

    # ==========================================================
    # CAN COMPLETE MOVE
    # ==========================================================

    @staticmethod
    def can_complete_move(
        waybill_id,
    ):
        """
        Validate whether a Waybill can be completed.

        This method does not modify the database.

        Returns:

            tuple[bool, str]
        """

        if waybill_id is None:

            return (
                False,
                "No Waybill was selected.",
            )

        with SessionLocal() as session:

            waybill = session.get(
                Waybill,
                waybill_id,
            )

            if waybill is None:

                return (
                    False,
                    f"Waybill {waybill_id} was not found.",
                )

            session_error = (
                SwitchListMoveService.validate_active_operations_session(
                    waybill,
                    session,
                )
            )

            if session_error is not None:
                return False, session_error

            #
            # Only ACTIVE and IN_PROGRESS Waybills
            # may be completed.
            #

            if waybill.status not in (
                "ACTIVE",
                "IN_PROGRESS",
            ):

                return (
                    False,
                    (
                        f"Waybill status is "
                        f"'{waybill.status}' and "
                        f"cannot be completed."
                    ),
                )

            #
            # Load the car.
            #

            car = session.get(
                Car,
                waybill.car_id,
            )

            if car is None:

                return (
                    False,
                    "The car assigned to this Waybill "
                    "was not found.",
                )

            #
            # A Waybill needs a destination spot
            # for an actual physical set-out.
            #

            destination_spot_id = (
                waybill.destination_spot_id
            )

            if destination_spot_id is None:

                validation_error = (
                    SwitchListMoveService.validate_general_destination(
                        car,
                        waybill,
                        session,
                    )
                )

                if validation_error is not None:
                    return False, validation_error

                return True, "Move can be completed."

            #
            # Load destination spot.
            #

            from modelrailroadops.models.spot import (
                Spot,
            )

            destination_spot = session.get(
                Spot,
                destination_spot_id,
            )

            if destination_spot is None:

                return (
                    False,
                    "The destination spot was not found.",
                )

            #
            # Make sure the destination spot is empty.
            #

            occupying_car = (
                session.execute(
                    select(Car).where(
                        Car.spot_id
                        == destination_spot.id,
                        Car.id
                        != car.id,
                    )
                )
                .scalars()
                .first()
            )

            if occupying_car is not None:

                return (
                    False,
                    (
                        f"Destination Spot "
                        f"{destination_spot.spot_number} "
                        f"is occupied by "
                        f"{occupying_car.reporting_mark} "
                        f"{occupying_car.number}."
                    ),
                )

            #
            # Validate the car against the spot.
            #

            validation_error = (
                SwitchListMoveService.validate_spot(
                    car,
                    destination_spot,
                )
            )

            if validation_error is not None:

                return (
                    False,
                    validation_error,
                )

            return (
                True,
                "Move can be completed.",
            )

    # ==========================================================
    # COMPLETE MOVE
    # ==========================================================

    @staticmethod
    def complete_move(
        waybill_id,
    ):
        """
        Complete a Waybill move.

        The car is moved to the Waybill destination
        Industry / Track / Spot.

        The Waybill status is changed to COMPLETED.

        The resulting CarMovement record is associated
        with the Waybill's Operations Session.

        CarLocationService is responsible for updating
        the car's Industry / Track / Spot fields and
        recording the movement history.

        Returns:

            tuple[bool, str]
        """

        if waybill_id is None:

            return (
                False,
                "No Waybill was selected.",
            )

        with SessionLocal() as session:

            waybill = session.get(
                Waybill,
                waybill_id,
            )

            if waybill is None:

                return (
                    False,
                    f"Waybill {waybill_id} was not found.",
                )

            session_error = (
                SwitchListMoveService.validate_active_operations_session(
                    waybill,
                    session,
                )
            )

            if session_error is not None:
                return False, session_error

            #
            # Only ACTIVE and IN_PROGRESS Waybills
            # may be completed.
            #

            if waybill.status not in (
                "ACTIVE",
                "IN_PROGRESS",
            ):

                return (
                    False,
                    (
                        f"Waybill status is "
                        f"'{waybill.status}' and "
                        f"cannot be completed."
                    ),
                )

            #
            # Load the car.
            #

            car = session.get(
                Car,
                waybill.car_id,
            )

            if car is None:

                return (
                    False,
                    "The car assigned to this Waybill "
                    "was not found.",
                )

            #
            # Destination spot is required.
            #

            destination_spot_id = (
                waybill.destination_spot_id
            )

            if destination_spot_id is None:

                validation_error = (
                    SwitchListMoveService.validate_general_destination(
                        car,
                        waybill,
                        session,
                    )
                )

                if validation_error is not None:
                    return False, validation_error

                success, message = (
                    CarLocationService.move_car_to_location_track_with_message(
                        car.id,
                        waybill.destination_location_track_id,
                        waybill.operations_session_id,
                    )
                )

                if not success:
                    return False, message or "The car could not be moved."

                completed_at = datetime.utcnow()
                waybill.status = "COMPLETED"
                waybill.completed_at = completed_at

                generated_moves = session.execute(
                    select(CarMove).where(
                        CarMove.operations_session_id
                        == waybill.operations_session_id,
                        CarMove.waybill_id == waybill.id,
                        CarMove.status == "PENDING",
                    )
                ).scalars().all()

                for move in generated_moves:
                    move.status = "COMPLETED"
                    move.completed_at = completed_at

                session.commit()
                return True, "Move completed successfully."

            #
            # Load destination spot.
            #

            from modelrailroadops.models.spot import (
                Spot,
            )

            destination_spot = session.get(
                Spot,
                destination_spot_id,
            )

            if destination_spot is None:

                return (
                    False,
                    "The destination spot was not found.",
                )

            #
            # Make sure another car does not already
            # occupy the destination spot.
            #

            occupying_car = (
                session.execute(
                    select(Car).where(
                        Car.spot_id
                        == destination_spot.id,
                        Car.id
                        != car.id,
                    )
                )
                .scalars()
                .first()
            )

            if occupying_car is not None:

                return (
                    False,
                    (
                        f"Destination Spot "
                        f"{destination_spot.spot_number} "
                        f"is occupied by "
                        f"{occupying_car.reporting_mark} "
                        f"{occupying_car.number}."
                    ),
                )

            #
            # Validate spot restrictions.
            #

            validation_error = (
                SwitchListMoveService.validate_spot(
                    car,
                    destination_spot,
                )
            )

            if validation_error is not None:

                return (
                    False,
                    validation_error,
                )

            #
            # Move the car.
            #
            # Pass the Operations Session ID so the
            # resulting CarMovement history record
            # belongs to this operating session.
            #

            try:

                moved_car = (
                    CarLocationService.move_car(
                        car.id,
                        destination_spot.id,
                        waybill.operations_session_id,
                    )
                )

            except Exception as ex:

                return (
                    False,
                    (
                        "The car could not be moved: "
                        f"{ex}"
                    ),
                )

            #
            # CarLocationService returns False when
            # the move fails.
            #

            if moved_car is False:

                return (
                    False,
                    "The car could not be moved.",
                )

            #
            # Mark the Waybill and its generated operating
            # instructions completed.  A switch-list completion
            # performs the complete origin-to-destination move,
            # so both its PICKUP and SETOUT records are complete.
            #

            completed_at = datetime.utcnow()

            waybill.status = "COMPLETED"

            waybill.completed_at = completed_at

            generated_moves = (
                session.execute(
                    select(
                        CarMove
                    ).where(
                        CarMove.operations_session_id
                        == waybill.operations_session_id,
                        CarMove.waybill_id
                        == waybill.id,
                        CarMove.status
                        == "PENDING",
                    )
                )
                .scalars()
                .all()
            )

            for move in generated_moves:

                move.status = "COMPLETED"

                move.completed_at = completed_at

            session.commit()

            return (
                True,
                "Move completed successfully.",
            )
