from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car_move import CarMove
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

        Completed instructions are retained so the switch-list
        data layer can report their status while the associated
        Waybill remains active or in progress.

        Only CarMoves whose Waybill remains ACTIVE or
        IN_PROGRESS are included in the active switch list.
        """

        if operations_session_id is None:
            return []

        with SessionLocal() as session:
            filters = [
                CarMove.operations_session_id
                == operations_session_id,
                Waybill.status.in_(
                    SwitchListService.ACTIVE_STATUSES
                ),
            ]

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