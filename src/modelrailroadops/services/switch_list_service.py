from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car_movement import CarMovement
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.waybill import Waybill


class SwitchListService:
    """
    Build operator-facing switch-list data from generated
    CarMove instructions.

    Each switch-list row represents one CarMove:

        PICKUP
            Pick up the car at the Waybill origin.

        SETOUT
            Set out the car at the Waybill destination.

    Switch-list data may be returned for an entire
    Operations Session or filtered to one Train.

    The service does not move cars or modify Waybills.
    """

    ACTIVE_STATUSES = (
        "ACTIVE",
        "IN_PROGRESS",
    )

    @staticmethod
    def check_session_consistency(operations_session_id):
        """Find legacy state conflicts without changing any data."""

        with SessionLocal() as session:
            operations_session = session.get(
                OperationsSession,
                operations_session_id,
            )
            if operations_session is None:
                return None

            moves = session.execute(
                select(CarMove).where(
                    CarMove.operations_session_id
                    == operations_session_id
                ).order_by(CarMove.id)
            ).scalars().all()
            history_count = len(session.execute(
                select(CarMovement).where(
                    CarMovement.operations_session_id
                    == operations_session_id
                )
            ).scalars().all())

            pending_moves = [
                move for move in moves
                if move.status != "COMPLETED"
            ]
            detached_waybill_moves = [
                move for move in moves
                if (
                    move.waybill is None
                    or move.waybill.operations_session_id
                    != operations_session_id
                )
            ]
            completed_waybill_pending_moves = [
                move for move in pending_moves
                if (
                    move.waybill is not None
                    and move.waybill.status == "COMPLETED"
                )
            ]

            issues = []
            if (
                operations_session.status == "COMPLETED"
                and operations_session.completed_at is None
            ):
                issues.append(
                    "The completed session has no completion timestamp."
                )
            if (
                operations_session.status == "COMPLETED"
                and pending_moves
            ):
                issues.append(
                    f"{len(pending_moves)} generated move(s) are still PENDING."
                )
            if completed_waybill_pending_moves:
                issues.append(
                    f"{len(completed_waybill_pending_moves)} pending move(s) "
                    "belong to completed waybills."
                )
            if detached_waybill_moves:
                issues.append(
                    f"{len(detached_waybill_moves)} move(s) reference a waybill "
                    "assigned to another session or no longer available."
                )
            if moves and history_count == 0:
                issues.append(
                    "Generated moves exist, but no car-movement history was recorded."
                )

            return {
                "operations_session_id": operations_session.id,
                "session_name": operations_session.name,
                "session_status": operations_session.status,
                "issues": issues,
                "move_count": len(moves),
                "pending_move_count": len(pending_moves),
                "pending_move_ids": [move.id for move in pending_moves],
                "detached_waybill_move_count": len(detached_waybill_moves),
                "history_count": history_count,
                "can_remove_stale_pending_moves": (
                    operations_session.status == "COMPLETED"
                    and bool(pending_moves)
                ),
            }

    @staticmethod
    def remove_stale_pending_moves(operations_session_id):
        """Remove only pending instructions from a completed legacy session."""

        with SessionLocal() as session:
            operations_session = session.get(
                OperationsSession,
                operations_session_id,
            )
            if operations_session is None:
                return False, "The Operations Session was not found."
            if operations_session.status != "COMPLETED":
                return (
                    False,
                    "Stale moves can be removed only from a completed session.",
                )

            pending_moves = session.execute(
                select(CarMove).where(
                    CarMove.operations_session_id == operations_session_id,
                    CarMove.status != "COMPLETED",
                )
            ).scalars().all()
            if not pending_moves:
                return False, "No stale pending moves were found."

            count = len(pending_moves)
            for move in pending_moves:
                session.delete(move)
            session.commit()

            return (
                True,
                f"Removed {count} stale pending move instruction(s). "
                "Waybills, car locations, and car history were not changed.",
            )

    @staticmethod
    def get_completed_session_report(
        operations_session_id,
        train_id=None,
    ):
        """Return a read-only summary of an operating session."""

        rows = SwitchListService.get_switch_list_rows(
            operations_session_id,
            train_id=train_id,
        )

        with SessionLocal() as session:
            operations_session = session.get(
                OperationsSession,
                operations_session_id,
            )

            if operations_session is None:
                return None

            return_count = session.execute(
                select(CarMovement).where(
                    CarMovement.operations_session_id
                    == operations_session_id,
                    CarMovement.movement_type == "RETURN",
                )
            ).scalars().all()

            session_data = {
                "operations_session_id": operations_session.id,
                "session_name": (
                    operations_session.name
                    or f"Session {operations_session.id}"
                ),
                "session_date": operations_session.session_date,
                "session_status": operations_session.status or "",
                "completed_at": operations_session.completed_at,
            }

        completed_moves = [
            row for row in rows
            if row.get("move_status") == "COMPLETED"
        ]
        pending_moves = [
            row for row in rows
            if row.get("move_status") != "COMPLETED"
        ]
        pickups = [
            row for row in rows
            if row.get("move_type") == "PICKUP"
        ]
        setouts = [
            row for row in rows
            if row.get("move_type") == "SETOUT"
        ]

        cars = {}
        for row in rows:
            cars[row["car_id"]] = {
                "car_id": row["car_id"],
                "car": row.get("car", ""),
                "car_type": row.get("car_type", ""),
                "train": row.get("train", ""),
                "final_location": row.get(
                    "current_location",
                    "Unassigned",
                ),
                "on_train": row.get(
                    "current_location",
                    "",
                ).startswith("On Train:"),
            }

        car_rows = sorted(
            cars.values(),
            key=lambda row: (
                row["train"].casefold(),
                row["car"].casefold(),
            ),
        )
        trains = sorted({
            row.get("train", "")
            for row in rows
            if row.get("train")
        }, key=str.casefold)

        return {
            **session_data,
            "train_id": train_id,
            "trains": trains,
            "total_moves": len(rows),
            "pickup_count": len(pickups),
            "setout_count": len(setouts),
            "completed_count": len(completed_moves),
            "pending_count": len(pending_moves),
            "return_count": len(return_count),
            "on_train_count": sum(
                1 for row in car_rows if row["on_train"]
            ),
            "cars": car_rows,
        }

    # ==========================================================
    # WAYBILL LOAD OPTIONS
    # ==========================================================

    @staticmethod
    def _load_options():
        """
        Return relationship loading options required when
        loading Waybills directly.
        """

        return (
            joinedload(
                Waybill.car
            ),
            joinedload(
                Waybill.operations_session
            ),
            joinedload(
                Waybill.origin_industry
            ),
            joinedload(
                Waybill.origin_track
            ),
            joinedload(
                Waybill.origin_spot
            ),
            joinedload(
                Waybill.origin_operating_location
            ),
            joinedload(
                Waybill.origin_operating_track
            ),
            joinedload(
                Waybill.destination_industry
            ),
            joinedload(
                Waybill.destination_track
            ),
            joinedload(
                Waybill.destination_spot
            ),
            joinedload(
                Waybill.destination_operating_location
            ),
            joinedload(
                Waybill.destination_operating_track
            ),
        )

    # ==========================================================
    # CAR MOVE LOAD OPTIONS
    # ==========================================================

    @staticmethod
    def _move_load_options():
        """
        Return relationship loading options required for
        CarMove-driven switch-list rows.
        """

        return (
            joinedload(
                CarMove.train
            ),
            joinedload(
                CarMove.car
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.operations_session
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.origin_industry
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.origin_track
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.origin_spot
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.origin_operating_location
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.origin_operating_track
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.destination_industry
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.destination_track
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.destination_spot
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.destination_operating_location
            ),
            joinedload(
                CarMove.waybill
            ).joinedload(
                Waybill.destination_operating_track
            ),
        )

    # ==========================================================
    # LEGACY WAYBILL LIST
    # ==========================================================

    @staticmethod
    def get_switch_list(
        operations_session_id,
    ):
        """
        Return active and in-progress Waybills for an
        Operations Session.

        This method is retained for compatibility with code
        that still needs the underlying Waybill objects.

        Operator-facing switch-list rows are now generated
        by get_switch_list_rows() from CarMove records.
        """

        if operations_session_id is None:
            return []

        with SessionLocal() as session:
            statement = (
                select(
                    Waybill
                )
                .options(
                    *SwitchListService._load_options()
                )
                .where(
                    Waybill.operations_session_id
                    == operations_session_id,
                    Waybill.status.in_(
                        SwitchListService.ACTIVE_STATUSES
                    ),
                )
                .order_by(
                    Waybill.destination_industry_id,
                    Waybill.destination_track_id,
                    Waybill.destination_spot_id,
                    Waybill.car_id,
                )
            )

            return (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

    # ==========================================================
    # GENERATED CAR MOVES
    # ==========================================================

    @staticmethod
    def get_generated_moves(
        operations_session_id,
        train_id=None,
    ):
        """
        Return generated CarMove instructions for an
        Operations Session.

        If train_id is provided, return only CarMoves assigned
        to that Train.

        Completed instructions are retained for a COMPLETED
        Operations Session, including after its Waybills have
        been completed. CANCELLED Waybills are never included.

        For a non-completed Operations Session, only CarMoves
        whose Waybill remains ACTIVE or IN_PROGRESS are included.
        """

        if operations_session_id is None:
            return []

        with SessionLocal() as session:
            operations_session = session.get(
                OperationsSession,
                operations_session_id,
            )

            if operations_session is None:
                return []

            filters = [
                CarMove.operations_session_id
                == operations_session_id,
            ]

            if operations_session.status == "COMPLETED":
                filters.append(
                    Waybill.status != "CANCELLED"
                )

            else:
                filters.append(
                    Waybill.status.in_(
                        SwitchListService.ACTIVE_STATUSES
                    )
                )

            if train_id is not None:
                filters.append(
                    CarMove.train_id
                    == train_id
                )

            statement = (
                select(
                    CarMove
                )
                .join(
                    Waybill,
                    CarMove.waybill_id
                    == Waybill.id,
                )
                .options(
                    *SwitchListService._move_load_options()
                )
                .where(
                    *filters
                )
                .order_by(
                    CarMove.train_id,
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

    # ==========================================================
    # TRAIN DISPLAY
    # ==========================================================

    @staticmethod
    def _get_train_display(
        train,
    ):
        """
        Return the operator-facing Train identification.
        """

        if train is None:
            return ""

        symbol = (
            getattr(
                train,
                "symbol",
                "",
            )
            or ""
        )

        number = (
            getattr(
                train,
                "number",
                "",
            )
            or ""
        )

        name = (
            getattr(
                train,
                "name",
                "",
            )
            or ""
        )

        identifier = (
            symbol
            or number
        )

        if identifier and name:
            return (
                f"{identifier} - {name}"
            )

        return (
            identifier
            or name
        )

    # ==========================================================
    # ORIGIN DATA
    # ==========================================================

    @staticmethod
    def _get_origin_data(
        waybill,
    ):
        """
        Build structured and display origin information.
        """

        origin_industry = ""

        if waybill.origin_industry is not None:
            origin_industry = (
                waybill.origin_industry.name
                or ""
            )

        if (
            not origin_industry
            and waybill.origin_operating_location
            is not None
        ):
            origin_industry = (
                waybill.origin_operating_location.name
                or ""
            )

        origin_track = ""

        if waybill.origin_track is not None:
            origin_track = (
                waybill.origin_track.name
                or ""
            )

        if (
            not origin_track
            and waybill.origin_operating_track
            is not None
        ):
            origin_track = (
                waybill.origin_operating_track.name
                or ""
            )

        origin_spot = ""

        if waybill.origin_spot is not None:
            origin_spot = str(
                waybill.origin_spot.spot_number
            )

        if origin_industry:
            origin_display = (
                origin_industry
            )

            if origin_track:
                origin_display += (
                    f" - {origin_track}"
                )

            if origin_spot:
                origin_display += (
                    f" - Spot {origin_spot}"
                )

        else:
            origin_display = (
                waybill.origin_location
                or ""
            )

        return {
            "origin": origin_display,
            "origin_location": (
                waybill.origin_location
                or ""
            ),
            "origin_industry": origin_industry,
            "origin_track": origin_track,
            "origin_spot": origin_spot,
        }

    # ==========================================================
    # DESTINATION DATA
    # ==========================================================

    @staticmethod
    def _get_destination_data(
        waybill,
    ):
        """
        Build structured and display destination information.
        """

        destination_industry = ""

        if waybill.destination_industry is not None:
            destination_industry = (
                waybill.destination_industry.name
                or ""
            )

        if (
            not destination_industry
            and waybill.destination_operating_location
            is not None
        ):
            destination_industry = (
                waybill.destination_operating_location.name
                or ""
            )

        destination_track = ""

        if waybill.destination_track is not None:
            destination_track = (
                waybill.destination_track.name
                or ""
            )

        if (
            not destination_track
            and waybill.destination_operating_track
            is not None
        ):
            destination_track = (
                waybill.destination_operating_track.name
                or ""
            )

        destination_spot = ""

        if waybill.destination_spot is not None:
            destination_spot = str(
                waybill.destination_spot.spot_number
            )

        destination_display = (
            destination_industry
        )

        if destination_track:
            if destination_display:
                destination_display += (
                    f" - {destination_track}"
                )

            else:
                destination_display = (
                    destination_track
                )

        if destination_spot:
            if destination_display:
                destination_display += (
                    f" - Spot {destination_spot}"
                )

            else:
                destination_display = (
                    f"Spot {destination_spot}"
                )

        return {
            "destination": destination_display,
            "destination_industry": destination_industry,
            "destination_track": destination_track,
            "destination_spot": destination_spot,
        }

    # ==========================================================
    # OPERATOR LOCATION
    # ==========================================================

    @staticmethod
    def _get_instruction_location(
        move_type,
        origin_data,
        destination_data,
    ):
        """
        Return the physical location relevant to this
        individual operating instruction.

        PICKUP:
            Origin

        SETOUT:
            Destination
        """

        if move_type == "PICKUP":
            return (
                origin_data["origin"]
            )

        if move_type == "SETOUT":
            return (
                destination_data["destination"]
            )

        return ""

    # ==========================================================
    # SWITCH LIST ROWS
    # ==========================================================

    @staticmethod
    def get_switch_list_rows(
        operations_session_id,
        train_id=None,
    ):
        """
        Return operator-facing switch-list rows.

        Each row represents one generated CarMove rather
        than one Waybill.

        If train_id is provided, only rows assigned to that
        Train are returned.

        Important row keys include:

            car_move_id
            move_type
            move_status
            route_sequence
            train_id
            train
            waybill_id
            car_id
            car
            instruction_location

        Compatibility keys from the previous Waybill-driven
        switch list are retained where practical.
        """

        moves = (
            SwitchListService.get_generated_moves(
                operations_session_id,
                train_id=train_id,
            )
        )

        rows = []

        for move in moves:
            waybill = move.waybill
            car = move.car

            if (
                waybill is None
                or car is None
            ):
                continue

            train_display = (
                SwitchListService._get_train_display(
                    move.train
                )
            )

            origin_data = (
                SwitchListService._get_origin_data(
                    waybill
                )
            )

            destination_data = (
                SwitchListService._get_destination_data(
                    waybill
                )
            )

            car_name = (
                f"{car.reporting_mark} "
                f"{car.number}"
            )

            car_type = (
                car.car_type
                or ""
            )

            length = (
                car.length
                if car.length is not None
                else ""
            )

            route_sequence = (
                move.route_sequence
            )

            pickup_sequence = None
            setout_sequence = None

            if move.move_type == "PICKUP":
                pickup_sequence = (
                    route_sequence
                )

            elif move.move_type == "SETOUT":
                setout_sequence = (
                    route_sequence
                )

            instruction_location = (
                SwitchListService._get_instruction_location(
                    move.move_type,
                    origin_data,
                    destination_data,
                )
            )

            rows.append(
                {
                    "car_move_id": move.id,
                    "move_type": (
                        move.move_type
                        or ""
                    ),
                    "move_status": (
                        move.status
                        or ""
                    ),
                    "route_sequence": (
                        route_sequence
                    ),
                    "waybill_id": waybill.id,
                    "train_id": move.train_id,
                    "train": train_display,
                    "pickup_sequence": (
                        pickup_sequence
                    ),
                    "setout_sequence": (
                        setout_sequence
                    ),
                    "car_id": car.id,
                    "car": car_name,
                    "reporting_mark": (
                        car.reporting_mark
                        or ""
                    ),
                    "number": (
                        car.number
                        or ""
                    ),
                    "car_type": car_type,
                    "length": length,
                    "status": (
                        car.status
                        or ""
                    ),
                    "current_location": (
                        car.location
                        or "Unassigned"
                    ),
                    "instruction_location": (
                        instruction_location
                    ),
                    "origin": (
                        origin_data["origin"]
                    ),
                    "origin_location": (
                        origin_data["origin_location"]
                    ),
                    "origin_industry": (
                        origin_data["origin_industry"]
                    ),
                    "origin_track": (
                        origin_data["origin_track"]
                    ),
                    "origin_spot": (
                        origin_data["origin_spot"]
                    ),
                    "destination": (
                        destination_data["destination"]
                    ),
                    "destination_industry": (
                        destination_data[
                            "destination_industry"
                        ]
                    ),
                    "destination_track": (
                        destination_data[
                            "destination_track"
                        ]
                    ),
                    "destination_spot": (
                        destination_data[
                            "destination_spot"
                        ]
                    ),
                    "waybill_status": (
                        waybill.status
                        or ""
                    ),
                    "notes": (
                        waybill.notes
                        or ""
                    ),
                    "move_notes": (
                        move.notes
                        or ""
                    ),
                }
            )

        rows.sort(
            key=lambda row: (
                (
                    row["train"]
                    or "Unassigned"
                ).casefold(),
                (
                    row["route_sequence"]
                    if row["route_sequence"] is not None
                    else 999999
                ),
                (
                    0
                    if row["move_type"] == "PICKUP"
                    else 1
                ),
                row["reporting_mark"].casefold(),
                row["number"].casefold(),
                row["car_move_id"],
            )
        )

        return rows

    # ==========================================================
    # PICKUP ROWS
    # ==========================================================

    @staticmethod
    def get_pickup_rows(
        operations_session_id,
        train_id=None,
    ):
        """
        Return only PICKUP CarMove rows.

        If train_id is provided, only PICKUP rows assigned
        to that Train are returned.

        Rows are ordered by Train, route sequence, physical
        pickup location, and car identification.
        """

        rows = (
            SwitchListService.get_switch_list_rows(
                operations_session_id,
                train_id=train_id,
            )
        )

        pickup_rows = [
            row
            for row in rows
            if row["move_type"] == "PICKUP"
        ]

        pickup_rows.sort(
            key=lambda row: (
                (
                    row["train"]
                    or "Unassigned"
                ).casefold(),
                (
                    row["route_sequence"]
                    if row["route_sequence"] is not None
                    else 999999
                ),
                row["origin_industry"].casefold(),
                row["origin_track"].casefold(),
                (
                    int(row["origin_spot"])
                    if row["origin_spot"].isdigit()
                    else 0
                ),
                row["reporting_mark"].casefold(),
                row["number"].casefold(),
            )
        )

        return pickup_rows

    # ==========================================================
    # SETOUT ROWS
    # ==========================================================

    @staticmethod
    def get_setout_rows(
        operations_session_id,
        train_id=None,
    ):
        """
        Return only SETOUT CarMove rows.

        If train_id is provided, only SETOUT rows assigned
        to that Train are returned.

        Rows are ordered by Train, route sequence, destination,
        and car identification.
        """

        rows = (
            SwitchListService.get_switch_list_rows(
                operations_session_id,
                train_id=train_id,
            )
        )

        setout_rows = [
            row
            for row in rows
            if row["move_type"] == "SETOUT"
        ]

        setout_rows.sort(
            key=lambda row: (
                (
                    row["train"]
                    or "Unassigned"
                ).casefold(),
                (
                    row["route_sequence"]
                    if row["route_sequence"] is not None
                    else 999999
                ),
                row["destination_industry"].casefold(),
                row["destination_track"].casefold(),
                (
                    int(row["destination_spot"])
                    if row["destination_spot"].isdigit()
                    else 0
                ),
                row["reporting_mark"].casefold(),
                row["number"].casefold(),
            )
        )

        return setout_rows

    # ==========================================================
    # CARS CURRENTLY ON TRAINS
    # ==========================================================

    @staticmethod
    def get_on_train_rows(
        operations_session_id,
        train_id=None,
    ):
        """Return cars picked up but not yet set out.

        Each result is based on a pending SETOUT instruction and
        the car's current On Train location. The existing move
        validator supplies the operator-facing readiness state.
        """

        from modelrailroadops.services.switch_list_move_service import (
            SwitchListMoveService,
        )

        setout_rows = SwitchListService.get_setout_rows(
            operations_session_id,
            train_id=train_id,
        )

        on_train_rows = []

        for row in setout_rows:
            if row["move_status"] != "PENDING":
                continue

            current_location = row.get(
                "current_location",
                "",
            )

            if not current_location.startswith("On Train:"):
                continue

            can_setout, message = (
                SwitchListMoveService.can_complete_move(
                    row["car_move_id"]
                )
            )

            on_train_row = dict(row)
            on_train_row["can_setout"] = can_setout
            on_train_row["setout_status"] = (
                "Ready"
                if can_setout
                else message
            )
            on_train_rows.append(on_train_row)

        return on_train_rows
