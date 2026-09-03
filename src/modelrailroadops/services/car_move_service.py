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
    # Calculate the tonnage of a CarMove.
    #
    # Weight comes from:
    #
    #     Car.empty_weight_lbs
    #
    # plus:
    #
    #     Waybill.cargo_weight_lbs
    #
    # for loaded cars.
    #

    @staticmethod
    def get_move_tonnage(
        move,
    ):

        if move is None:

            return None

        car = getattr(
            move,
            "car",
            None,
        )

        waybill = getattr(
            move,
            "waybill",
            None,
        )

        if (
            car is None
            or waybill is None
        ):

            return None

        empty_weight_lbs = getattr(
            car,
            "empty_weight_lbs",
            None,
        )

        if empty_weight_lbs is None:

            return None

        load_state = (
            getattr(
                waybill,
                "load_state",
                None,
            )
            or ""
        ).strip().upper()

        if load_state == "EMPTY":

            gross_weight_lbs = (
                empty_weight_lbs
            )

        elif load_state == "LOADED":

            cargo_weight_lbs = getattr(
                waybill,
                "cargo_weight_lbs",
                None,
            )

            if cargo_weight_lbs is None:

                return None

            gross_weight_lbs = (
                empty_weight_lbs
                + cargo_weight_lbs
            )

        else:

            return None

        return (
            gross_weight_lbs
            / 2000.0
        )

    #
    # Calculate the maximum train size and tonnage
    # encountered while operating a Train during an
    # Operations Session.
    #
    # At each route sequence:
    #
    #     SETOUT moves are processed first.
    #     PICKUP moves are processed second.
    #
    # This represents the consist departing each stop
    # after switching has been completed.
    #
    # The returned maximum tonnage includes only cars
    # whose weight can be calculated. Cars with missing
    # weight information are counted separately.
    #

    @staticmethod
    def get_train_weight_summary(
        operations_session_id,
        train_id,
    ):

        if (
            operations_session_id is None
            or train_id is None
        ):

            return {
                "maximum_car_count": 0,
                "maximum_tonnage": 0.0,
                "missing_weight_count": 0,
            }

        moves = (
            CarMoveService.get_by_operations_session_and_train(
                operations_session_id,
                train_id,
            )
        )

        if not moves:

            return {
                "maximum_car_count": 0,
                "maximum_tonnage": 0.0,
                "missing_weight_count": 0,
            }

        #
        # Sort moves explicitly so SETOUT moves occur before
        # PICKUP moves at the same route sequence.
        #

        def move_sort_key(move):

            route_sequence = getattr(
                move,
                "route_sequence",
                None,
            )

            if route_sequence is None:

                route_sequence = 0

            move_type = (
                getattr(
                    move,
                    "move_type",
                    "",
                )
                or ""
            ).strip().upper()

            move_type_order = (
                0
                if move_type == "SETOUT"
                else 1
            )

            return (
                route_sequence,
                move_type_order,
                move.id,
            )

        ordered_moves = sorted(
            moves,
            key=move_sort_key,
        )

        active_cars = {}

        maximum_car_count = 0
        maximum_tonnage = 0.0

        missing_weight_car_ids = set()

        current_route_sequence = None

        for move in ordered_moves:

            route_sequence = getattr(
                move,
                "route_sequence",
                None,
            )

            #
            # When moving to the next route sequence,
            # record the departing consist from the
            # previous stop.
            #

            if (
                current_route_sequence is not None
                and route_sequence
                != current_route_sequence
            ):

                current_car_count = len(
                    active_cars
                )

                current_tonnage = sum(
                    tonnage
                    for tonnage in active_cars.values()
                    if tonnage is not None
                )

                maximum_car_count = max(
                    maximum_car_count,
                    current_car_count,
                )

                maximum_tonnage = max(
                    maximum_tonnage,
                    current_tonnage,
                )

            current_route_sequence = (
                route_sequence
            )

            move_type = (
                getattr(
                    move,
                    "move_type",
                    "",
                )
                or ""
            ).strip().upper()

            car_id = getattr(
                move,
                "car_id",
                None,
            )

            if car_id is None:

                continue

            if move_type == "SETOUT":

                active_cars.pop(
                    car_id,
                    None,
                )

            elif move_type == "PICKUP":

                tonnage = (
                    CarMoveService.get_move_tonnage(
                        move
                    )
                )

                active_cars[car_id] = (
                    tonnage
                )

                if tonnage is None:

                    missing_weight_car_ids.add(
                        car_id
                    )

        #
        # Record the consist departing the final
        # route sequence.
        #

        current_car_count = len(
            active_cars
        )

        current_tonnage = sum(
            tonnage
            for tonnage in active_cars.values()
            if tonnage is not None
        )

        maximum_car_count = max(
            maximum_car_count,
            current_car_count,
        )

        maximum_tonnage = max(
            maximum_tonnage,
            current_tonnage,
        )

        return {
            "maximum_car_count": (
                maximum_car_count
            ),
            "maximum_tonnage": (
                maximum_tonnage
            ),
            "missing_weight_count": len(
                missing_weight_car_ids
            ),
        }

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