from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.waybill import Waybill

from modelrailroadops.services.car_location_service import (
    CarLocationService,
)

from modelrailroadops.services.car_move_service import (
    CarMoveService,
)


class SwitchListMoveService:
    """
    Service for validating and completing individual
    switch-list CarMove instructions.

    A generated Waybill normally produces two CarMove
    instructions:

        PICKUP
            The car is picked up by the assigned train.

        SETOUT
            The car is physically placed at its Waybill
            destination.

    PICKUP completion:

        - Starts a PLANNED Operations Session.
        - Marks only the PICKUP CarMove completed.
        - Changes the Waybill from ACTIVE to IN_PROGRESS.
        - Does not physically relocate the car.

    SETOUT completion:

        - Requires the corresponding PICKUP to be completed.
        - Validates the physical destination.
        - Physically relocates the car.
        - Records CarMovement history.
        - Marks only the SETOUT CarMove completed.
        - Completes the Waybill when no pending CarMoves remain.

    All database changes for one switch-list instruction
    are performed in one transaction.
    """

    # ==========================================================
    # VALIDATE OPERATIONS SESSION
    # ==========================================================

    @staticmethod
    def validate_active_operations_session(
        waybill,
        session,
    ):
        """
        Validate that the Waybill belongs to an Operations
        Session that may accept operating moves.
        """

        operations_session_id = getattr(
            waybill,
            "operations_session_id",
            None,
        )

        if operations_session_id is None:

            return (
                "This Waybill is not assigned to an "
                "Operations Session."
            )

        operations_session = session.get(
            OperationsSession,
            operations_session_id,
        )

        if operations_session is None:

            return (
                "The Waybill's Operations Session was not found."
            )

        if operations_session.status not in (
            "PLANNED",
            "ACTIVE",
        ):

            return (
                f"Operations Session "
                f"'{operations_session.name}' is "
                f"{operations_session.status} and "
                f"cannot accept car moves."
            )

        return None

    # ==========================================================
    # VALIDATE GENERAL DESTINATION
    # ==========================================================

    @staticmethod
    def validate_general_destination(
        car,
        waybill,
        session,
    ):
        """
        Validate a general yard, staging, or interchange
        destination that does not use an Industry Spot.
        """

        track_id = getattr(
            waybill,
            "destination_location_track_id",
            None,
        )

        location_id = getattr(
            waybill,
            "destination_location_id",
            None,
        )

        if (
            location_id is None
            or track_id is None
        ):

            return (
                "This Waybill does not have a complete destination."
            )

        location = session.get(
            Location,
            location_id,
        )

        track = session.get(
            LocationTrack,
            track_id,
        )

        if (
            location is None
            or track is None
            or track.location_id != location.id
        ):

            return (
                "The destination Location or Track was not found."
            )

        if (
            not location.active
            or not track.active
        ):

            return (
                "The destination Location and Track must be active."
            )

        if track.capacity is not None:

            occupied = len(
                session.execute(
                    select(
                        Car
                    ).where(
                        Car.operating_track_id
                        == track.id,
                        Car.id
                        != car.id,
                    )
                )
                .scalars()
                .all()
            )

            if occupied >= track.capacity:

                return (
                    "The destination track is at capacity."
                )

        return None

    # ==========================================================
    # VALIDATE SPOT
    # ==========================================================

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

            return (
                "Car was not found."
            )

        if spot is None:

            return (
                "Destination spot was not found."
            )

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
    # LOAD AND VALIDATE CAR MOVE
    # ==========================================================

    @staticmethod
    def _validate_car_move(
        car_move_id,
        session,
    ):
        """
        Load the selected CarMove and validate the common
        requirements shared by PICKUP and SETOUT.

        Returns:

            (True, car_move, waybill, car, operations_session)

        or:

            (False, message, None, None, None)
        """

        if car_move_id is None:

            return (
                False,
                "No Car Move was selected.",
                None,
                None,
                None,
            )

        car_move = session.get(
            CarMove,
            car_move_id,
        )

        if car_move is None:

            return (
                False,
                f"Car Move {car_move_id} was not found.",
                None,
                None,
                None,
            )

        if car_move.status == "COMPLETED":

            return (
                False,
                "This Car Move has already been completed.",
                None,
                None,
                None,
            )

        if car_move.status != "PENDING":

            return (
                False,
                (
                    "This Car Move cannot be completed "
                    f"because its status is "
                    f"'{car_move.status}'."
                ),
                None,
                None,
                None,
            )

        if car_move.move_type not in (
            "PICKUP",
            "SETOUT",
        ):

            return (
                False,
                (
                    "This Car Move has an unsupported "
                    f"move type: '{car_move.move_type}'."
                ),
                None,
                None,
                None,
            )

        waybill = session.get(
            Waybill,
            car_move.waybill_id,
        )

        if waybill is None:

            return (
                False,
                "The Waybill assigned to this Car Move was not found.",
                None,
                None,
                None,
            )

        if (
            car_move.operations_session_id
            != waybill.operations_session_id
        ):

            return (
                False,
                (
                    "The Car Move and Waybill are assigned "
                    "to different Operations Sessions."
                ),
                None,
                None,
                None,
            )

        session_error = (
            SwitchListMoveService.validate_active_operations_session(
                waybill,
                session,
            )
        )

        if session_error is not None:

            return (
                False,
                session_error,
                None,
                None,
                None,
            )

        operations_session = session.get(
            OperationsSession,
            waybill.operations_session_id,
        )

        if operations_session is None:

            return (
                False,
                "The Operations Session was not found.",
                None,
                None,
                None,
            )

        if waybill.status not in (
            "ACTIVE",
            "IN_PROGRESS",
        ):

            return (
                False,
                (
                    f"Waybill status is "
                    f"'{waybill.status}' and "
                    f"cannot accept Car Moves."
                ),
                None,
                None,
                None,
            )

        car = session.get(
            Car,
            car_move.car_id,
        )

        if car is None:

            return (
                False,
                (
                    "The car assigned to this Car Move "
                    "was not found."
                ),
                None,
                None,
                None,
            )

        if car.id != waybill.car_id:

            return (
                False,
                (
                    "The Car Move and Waybill are assigned "
                    "to different cars."
                ),
                None,
                None,
                None,
            )

        return (
            True,
            car_move,
            waybill,
            car,
            operations_session,
        )

    # ==========================================================
    # VALIDATE PICKUP ORDER
    # ==========================================================

    @staticmethod
    def _validate_setout_pickup(
        car_move,
        session,
    ):
        """
        Ensure that a SETOUT cannot be completed until the
        corresponding PICKUP has been completed.
        """

        pickup = (
            session.execute(
                select(
                    CarMove
                )
                .where(
                    CarMove.car_id
                    == car_move.car_id,
                    CarMove.waybill_id
                    == car_move.waybill_id,
                    CarMove.move_type
                    == "PICKUP",
                    CarMove.status
                    == "COMPLETED",
                )
                .order_by(
                    CarMove.id
                )
            )
            .scalars()
            .first()
        )

        if pickup is None:

            return (
                "The SETOUT cannot be completed until "
                "the PICKUP for this car and Waybill "
                "has been completed."
            )

        return None

    # ==========================================================
    # VALIDATE SETOUT DESTINATION
    # ==========================================================

    @staticmethod
    def _validate_setout_destination(
        car,
        waybill,
        session,
    ):
        """
        Validate the physical destination for a SETOUT.
        """

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

                return (
                    False,
                    validation_error,
                )

            return (
                True,
                "",
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

        occupying_car = (
            session.execute(
                select(
                    Car
                ).where(
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
            "",
        )

    # ==========================================================
    # CAN COMPLETE MOVE
    # ==========================================================

    @staticmethod
    def can_complete_move(
        car_move_id,
    ):
        """
        Validate whether an individual CarMove can be completed.

        This method does not modify the database.

        Returns:

            tuple[bool, str]
        """

        with SessionLocal() as session:

            (
                valid,
                result,
                waybill,
                car,
                operations_session,
            ) = (
                SwitchListMoveService._validate_car_move(
                    car_move_id,
                    session,
                )
            )

            if not valid:

                return (
                    False,
                    result,
                )

            car_move = result

            if car_move.move_type == "PICKUP":

                return (
                    True,
                    "PICKUP can be completed.",
                )

            pickup_error = (
                SwitchListMoveService._validate_setout_pickup(
                    car_move,
                    session,
                )
            )

            if pickup_error is not None:

                return (
                    False,
                    pickup_error,
                )

            destination_valid, message = (
                SwitchListMoveService._validate_setout_destination(
                    car,
                    waybill,
                    session,
                )
            )

            if not destination_valid:

                return (
                    False,
                    message,
                )

            return (
                True,
                "SETOUT can be completed.",
            )

    # ==========================================================
    # COMPLETE PICKUP
    # ==========================================================

    @staticmethod
    def _complete_pickup(
        car_move,
        waybill,
        operations_session,
        session,
    ):
        """
        Complete one PICKUP instruction.

        The car remains at its current physical database
        location because the application does not yet model
        an in-transit/train location.
        """

        if operations_session.status == "PLANNED":

            operations_session.status = "ACTIVE"

        success, result = (
            CarMoveService.complete(
                car_move.id,
                db_session=session,
            )
        )

        if not success:

            return (
                False,
                result,
            )

        if waybill.status == "ACTIVE":

            waybill.status = "IN_PROGRESS"

        return (
            True,
            "PICKUP completed successfully.",
        )

    # ==========================================================
    # COMPLETE SETOUT
    # ==========================================================

    @staticmethod
    def _complete_setout(
        car_move,
        waybill,
        car,
        session,
    ):
        """
        Complete one SETOUT instruction.

        The car is physically moved to the Waybill destination
        and the movement-history record is created in the same
        transaction as the CarMove and Waybill updates.
        """

        pickup_error = (
            SwitchListMoveService._validate_setout_pickup(
                car_move,
                session,
            )
        )

        if pickup_error is not None:

            return (
                False,
                pickup_error,
            )

        destination_valid, message = (
            SwitchListMoveService._validate_setout_destination(
                car,
                waybill,
                session,
            )
        )

        if not destination_valid:

            return (
                False,
                message,
            )

        destination_spot_id = (
            waybill.destination_spot_id
        )

        if destination_spot_id is None:

            success, message = (
                CarLocationService.move_car_to_location_track_with_message(
                    car.id,
                    waybill.destination_location_track_id,
                    waybill.operations_session_id,
                    db_session=session,
                )
            )

        else:

            success, message = (
                CarLocationService.assign_car_to_spot_with_message(
                    car.id,
                    destination_spot_id,
                    waybill.operations_session_id,
                    db_session=session,
                )
            )

        if not success:

            return (
                False,
                message or "The car could not be moved.",
            )

        success, result = (
            CarMoveService.complete(
                car_move.id,
                db_session=session,
            )
        )

        if not success:

            return (
                False,
                result,
            )

        completed_move = result

        #
        # Flush the completed SETOUT before checking whether
        # any pending instructions remain for this Waybill.
        #

        session.flush()

        pending_move = (
            session.execute(
                select(
                    CarMove
                )
                .where(
                    CarMove.operations_session_id
                    == waybill.operations_session_id,
                    CarMove.waybill_id
                    == waybill.id,
                    CarMove.status
                    == "PENDING",
                )
                .order_by(
                    CarMove.id
                )
            )
            .scalars()
            .first()
        )

        if pending_move is None:

            waybill.status = "COMPLETED"

            waybill.completed_at = (
                completed_move.completed_at
            )

        else:

            waybill.status = "IN_PROGRESS"

        return (
            True,
            "SETOUT completed successfully.",
        )

    # ==========================================================
    # COMPLETE MOVE
    # ==========================================================

    @staticmethod
    def complete_move(
        car_move_id,
    ):
        """
        Complete an individual switch-list CarMove.

        PICKUP:

            - Completes only the PICKUP instruction.
            - Starts a PLANNED Operations Session.
            - Changes an ACTIVE Waybill to IN_PROGRESS.
            - Does not physically relocate the car.

        SETOUT:

            - Requires a completed PICKUP.
            - Validates the destination.
            - Physically relocates the car.
            - Records CarMovement history.
            - Completes only the SETOUT instruction.
            - Completes the Waybill when all instructions
              have been completed.

        All changes occur in one transaction.

        Returns:

            tuple[bool, str]
        """

        session = SessionLocal()

        try:

            (
                valid,
                result,
                waybill,
                car,
                operations_session,
            ) = (
                SwitchListMoveService._validate_car_move(
                    car_move_id,
                    session,
                )
            )

            if not valid:

                session.rollback()

                return (
                    False,
                    result,
                )

            car_move = result

            if car_move.move_type == "PICKUP":

                success, message = (
                    SwitchListMoveService._complete_pickup(
                        car_move,
                        waybill,
                        operations_session,
                        session,
                    )
                )

            else:

                success, message = (
                    SwitchListMoveService._complete_setout(
                        car_move,
                        waybill,
                        car,
                        session,
                    )
                )

            if not success:

                session.rollback()

                return (
                    False,
                    message,
                )

            session.commit()

            return (
                True,
                message,
            )

        except Exception as exc:

            session.rollback()

            return (
                False,
                str(exc),
            )

        finally:

            session.close()