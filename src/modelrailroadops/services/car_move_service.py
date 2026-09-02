from datetime import datetime

from sqlalchemy import (
    select,
)

from sqlalchemy.orm import (
    joinedload,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car_move import CarMove


class CarMoveService:
    """
    Service used to create and manage CarMove records.

    CarMove records represent individual car movement
    instructions generated for an Operations Session.

    A CarMove has:

        - A move type:
            PICKUP
            SETOUT

        - An execution status:
            PENDING
            COMPLETED

    This service records the completion of the operating
    instruction. Physical car movement is handled by
    CarLocationService.
    """

    #
    # Get move by ID.
    #

    @staticmethod
    def get_by_id(
        move_id,
    ):

        if move_id is None:

            return None

        with SessionLocal() as session:

            statement = (
                select(
                    CarMove
                )
                .options(
                    joinedload(
                        CarMove.train
                    ),
                    joinedload(
                        CarMove.car
                    ),
                    joinedload(
                        CarMove.waybill
                    ),
                )
                .where(
                    CarMove.id
                    == move_id
                )
            )

            return (
                session.execute(
                    statement
                )
                .scalars()
                .first()
            )

    #
    # Get all moves.
    #

    @staticmethod
    def get_all():

        with SessionLocal() as session:

            statement = (
                select(
                    CarMove
                )
                .options(
                    joinedload(
                        CarMove.train
                    ),
                    joinedload(
                        CarMove.car
                    ),
                    joinedload(
                        CarMove.waybill
                    ),
                )
                .order_by(
                    CarMove.operations_session_id,
                    CarMove.route_sequence,
                    CarMove.id,
                )
            )

            return (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

    #
    # Get moves for an Operations Session.
    #

    @staticmethod
    def get_by_operations_session(
        operations_session_id,
    ):

        if operations_session_id is None:

            return []

        with SessionLocal() as session:

            statement = (
                select(
                    CarMove
                )
                .options(
                    joinedload(
                        CarMove.train
                    ),
                    joinedload(
                        CarMove.car
                    ),
                    joinedload(
                        CarMove.waybill
                    ),
                )
                .where(
                    CarMove.operations_session_id
                    == operations_session_id
                )
                .order_by(
                    CarMove.route_sequence,
                    CarMove.id,
                )
            )

            return (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

    #
    # Get moves for a Train.
    #

    @staticmethod
    def get_by_train(
        train_id,
    ):

        if train_id is None:

            return []

        with SessionLocal() as session:

            statement = (
                select(
                    CarMove
                )
                .options(
                    joinedload(
                        CarMove.train
                    ),
                    joinedload(
                        CarMove.car
                    ),
                    joinedload(
                        CarMove.waybill
                    ),
                )
                .where(
                    CarMove.train_id
                    == train_id
                )
                .order_by(
                    CarMove.route_sequence,
                    CarMove.id,
                )
            )

            return (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

    #
    # Get moves for an Operations Session
    # and Train.
    #

    @staticmethod
    def get_by_operations_session_and_train(
        operations_session_id,
        train_id,
    ):

        if (
            operations_session_id is None
            or train_id is None
        ):

            return []

        with SessionLocal() as session:

            statement = (
                select(
                    CarMove
                )
                .options(
                    joinedload(
                        CarMove.train
                    ),
                    joinedload(
                        CarMove.car
                    ),
                    joinedload(
                        CarMove.waybill
                    ),
                )
                .where(
                    CarMove.operations_session_id
                    == operations_session_id,
                    CarMove.train_id
                    == train_id,
                )
                .order_by(
                    CarMove.route_sequence,
                    CarMove.id,
                )
            )

            return (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

    #
    # Get pending moves for an Operations Session.
    #

    @staticmethod
    def get_pending_by_operations_session(
        operations_session_id,
    ):

        if operations_session_id is None:

            return []

        with SessionLocal() as session:

            statement = (
                select(
                    CarMove
                )
                .options(
                    joinedload(
                        CarMove.train
                    ),
                    joinedload(
                        CarMove.car
                    ),
                    joinedload(
                        CarMove.waybill
                    ),
                )
                .where(
                    CarMove.operations_session_id
                    == operations_session_id,
                    CarMove.status
                    == "PENDING",
                )
                .order_by(
                    CarMove.route_sequence,
                    CarMove.id,
                )
            )

            return (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

    #
    # Create move.
    #

    @staticmethod
    def create(
        operations_session_id,
        train_id,
        car_id,
        waybill_id,
        move_type,
        route_sequence=None,
        origin_location=None,
        destination_location=None,
        notes=None,
    ):

        if operations_session_id is None:

            return (
                False,
                "Operations Session is required.",
            )

        if train_id is None:

            return (
                False,
                "Train is required.",
            )

        if car_id is None:

            return (
                False,
                "Car is required.",
            )

        if waybill_id is None:

            return (
                False,
                "Waybill is required.",
            )

        if not move_type:

            return (
                False,
                "Move type is required.",
            )

        move_type = (
            str(
                move_type
            )
            .strip()
            .upper()
        )

        if move_type not in (
            "PICKUP",
            "SETOUT",
        ):

            return (
                False,
                (
                    "Move type must be "
                    "PICKUP or SETOUT."
                ),
            )

        with SessionLocal() as session:

            move = CarMove(
                operations_session_id=(
                    operations_session_id
                ),
                train_id=train_id,
                car_id=car_id,
                waybill_id=waybill_id,
                route_sequence=route_sequence,
                move_type=move_type,
                status="PENDING",
                origin_location=(
                    origin_location
                ),
                destination_location=(
                    destination_location
                ),
                notes=notes,
            )

            session.add(
                move
            )

            try:

                session.commit()

                session.refresh(
                    move
                )

            except Exception as exc:

                session.rollback()

                return (
                    False,
                    str(exc),
                )

            #
            # Load the related Train, Car, and Waybill
            # while the session is still active.
            #

            statement = (
                select(
                    CarMove
                )
                .options(
                    joinedload(
                        CarMove.train
                    ),
                    joinedload(
                        CarMove.car
                    ),
                    joinedload(
                        CarMove.waybill
                    ),
                )
                .where(
                    CarMove.id
                    == move.id
                )
            )

            move = (
                session.execute(
                    statement
                )
                .scalars()
                .first()
            )

            return (
                True,
                move,
            )

    #
    # Complete a CarMove.
    #

    @staticmethod
    def complete(
        move_id,
    ):

        if move_id is None:

            return (
                False,
                "Car Move ID is required.",
            )

        with SessionLocal() as session:

            move = session.get(
                CarMove,
                move_id,
            )

            if move is None:

                return (
                    False,
                    "Car Move not found.",
                )

            #
            # A completed move cannot be completed again.
            #

            if move.status == "COMPLETED":

                return (
                    False,
                    "This Car Move has already been completed.",
                )

            #
            # Only pending moves may be completed.
            #

            if move.status != "PENDING":

                return (
                    False,
                    (
                        "This Car Move cannot be completed "
                        f"because its status is "
                        f"{move.status}."
                    ),
                )

            #
            # A SETOUT cannot be completed until the
            # corresponding PICKUP has been completed.
            #
            # This prevents the operator from setting out
            # a car that has not yet been picked up.
            #

            if move.move_type == "SETOUT":

                pickup_statement = (
                    select(
                        CarMove
                    )
                    .where(
                        CarMove.car_id
                        == move.car_id,
                        CarMove.waybill_id
                        == move.waybill_id,
                        CarMove.move_type
                        == "PICKUP",
                        CarMove.status
                        == "COMPLETED",
                    )
                    .order_by(
                        CarMove.id
                    )
                )

                pickup = (
                    session.execute(
                        pickup_statement
                    )
                    .scalars()
                    .first()
                )

                if pickup is None:

                    return (
                        False,
                        (
                            "The SETOUT cannot be completed "
                            "until the PICKUP for this car "
                            "and waybill has been completed."
                        ),
                    )

            #
            # Mark the operating instruction complete.
            #

            move.status = "COMPLETED"

            move.completed_at = datetime.utcnow()

            try:

                session.commit()

                session.refresh(
                    move
                )

            except Exception as exc:

                session.rollback()

                return (
                    False,
                    str(exc),
                )

            return (
                True,
                move,
            )

    #
    # Delete move.
    #

    @staticmethod
    def delete(
        move_id,
    ):

        if move_id is None:

            return (
                False,
                "Car Move ID is required.",
            )

        with SessionLocal() as session:

            move = session.get(
                CarMove,
                move_id,
            )

            if move is None:

                return (
                    False,
                    "Car Move not found.",
                )

            session.delete(
                move
            )

            try:

                session.commit()

            except Exception as exc:

                session.rollback()

                return (
                    False,
                    str(exc),
                )

            return (
                True,
                None,
            )

    #
    # Delete all moves for an Operations Session.
    #

    @staticmethod
    def delete_by_operations_session(
        operations_session_id,
    ):

        if operations_session_id is None:

            return (
                False,
                "Operations Session ID is required.",
            )

        with SessionLocal() as session:

            statement = (
                select(
                    CarMove
                )
                .where(
                    CarMove.operations_session_id
                    == operations_session_id
                )
            )

            moves = (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

            for move in moves:

                session.delete(
                    move
                )

            try:

                session.commit()

            except Exception as exc:

                session.rollback()

                return (
                    False,
                    str(exc),
                )

            return (
                True,
                len(
                    moves
                ),
            )