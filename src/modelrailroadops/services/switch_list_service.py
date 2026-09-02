from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.waybill import Waybill


class SwitchListService:
    """
    Build switch-list data from Waybills.

    This service is responsible for retrieving the
    operational information needed to generate a
    switch list.

    It does not move cars or modify Waybills.
    """

    ACTIVE_STATUSES = (
        "ACTIVE",
        "IN_PROGRESS",
    )

    @staticmethod
    def get_generated_move_details(
        operations_session_id,
    ):
        """Return generated Train and route-order data by Waybill ID."""

        if operations_session_id is None:
            return {}

        with SessionLocal() as session:

            moves = (
                session.execute(
                    select(CarMove)
                    .options(
                        joinedload(CarMove.train)
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
                .scalars()
                .all()
            )

            details = {}

            for move in moves:

                detail = details.setdefault(
                    move.waybill_id,
                    {
                        "train_id": move.train_id,
                        "train": "",
                        "pickup_sequence": None,
                        "setout_sequence": None,
                    },
                )

                train = move.train

                if train is not None and not detail["train"]:

                    symbol = getattr(train, "symbol", "") or ""
                    name = getattr(train, "name", "") or ""

                    if symbol and name:
                        detail["train"] = f"{symbol} - {name}"
                    else:
                        detail["train"] = symbol or name

                if move.move_type == "PICKUP":
                    detail["pickup_sequence"] = move.route_sequence
                elif move.move_type == "SETOUT":
                    detail["setout_sequence"] = move.route_sequence

            return details

    @staticmethod
    def _load_options():
        """
        Return relationship loading options required
        by the switch-list data.
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

    @staticmethod
    def get_switch_list(
        operations_session_id,
    ):
        """
        Return active and in-progress Waybills for an
        Operations Session.

        The returned Waybill objects have all relationships
        needed by the switch-list UI loaded before the
        database session closes.

        Returns:

            list[Waybill]

        The list is ordered by:

            1. Destination Industry
            2. Destination Track
            3. Destination Spot
            4. Car reporting mark
            5. Car number
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

    @staticmethod
    def get_switch_list_rows(
        operations_session_id,
    ):
        """
        Return switch-list information as simple
        dictionaries.

        This method is intended for the switch-list
        table model, preview, printing, and export.

        It does not modify the database.
        """

        waybills = (
            SwitchListService.get_switch_list(
                operations_session_id
            )
        )

        generated_move_details = (
            SwitchListService.get_generated_move_details(
                operations_session_id
            )
        )

        rows = []

        for waybill in waybills:

            car = waybill.car

            if car is None:
                continue

            move_detail = generated_move_details.get(
                waybill.id,
                {},
            )

            #
            # Car identification
            #

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

            #
            # Origin
            #

            origin_industry = ""

            if waybill.origin_industry is not None:

                origin_industry = (
                    waybill.origin_industry.name
                    or ""
                )

            if not origin_industry and waybill.origin_operating_location is not None:

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

            if not origin_track and waybill.origin_operating_track is not None:

                origin_track = (
                    waybill.origin_operating_track.name
                    or ""
                )

            origin_spot = ""

            if waybill.origin_spot is not None:

                origin_spot = str(
                    waybill.origin_spot.spot_number
                )

            #
            # Destination
            #

            destination_industry = ""

            if (
                waybill.destination_industry
                is not None
            ):

                destination_industry = (
                    waybill.destination_industry.name
                    or ""
                )

            if (
                not destination_industry
                and waybill.destination_operating_location is not None
            ):

                destination_industry = (
                    waybill.destination_operating_location.name
                    or ""
                )

            destination_track = ""

            if (
                waybill.destination_track
                is not None
            ):

                destination_track = (
                    waybill.destination_track.name
                    or ""
                )

            if (
                not destination_track
                and waybill.destination_operating_track is not None
            ):

                destination_track = (
                    waybill.destination_operating_track.name
                    or ""
                )

            destination_spot = ""

            if (
                waybill.destination_spot
                is not None
            ):

                destination_spot = str(
                    waybill.destination_spot.spot_number
                )

            #
            # Origin display
            #

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

            #
            # Destination display
            #

            destination_display = (
                destination_industry
            )

            if destination_track:

                destination_display += (
                    f" - {destination_track}"
                )

            if destination_spot:

                destination_display += (
                    f" - Spot {destination_spot}"
                )

            #
            # Add switch-list row.
            #

            rows.append(
                {
                    "waybill_id": waybill.id,

                    "train_id": move_detail.get("train_id"),

                    "train": move_detail.get("train", ""),

                    "pickup_sequence": move_detail.get(
                        "pickup_sequence"
                    ),

                    "setout_sequence": move_detail.get(
                        "setout_sequence"
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

                    "origin": origin_display,

                    "origin_location": (
                        waybill.origin_location
                        or ""
                    ),

                    "origin_industry": (
                        origin_industry
                    ),

                    "origin_track": (
                        origin_track
                    ),

                    "origin_spot": (
                        origin_spot
                    ),

                    "destination": (
                        destination_display
                    ),

                    "destination_industry": (
                        destination_industry
                    ),

                    "destination_track": (
                        destination_track
                    ),

                    "destination_spot": (
                        destination_spot
                    ),

                    "waybill_status": (
                        waybill.status
                        or ""
                    ),

                    "notes": (
                        waybill.notes
                        or ""
                    ),
                }
            )

        rows.sort(
            key=lambda row: (
                (row["train"] or "Unassigned").casefold(),
                row["pickup_sequence"]
                if row["pickup_sequence"] is not None
                else 999999,
                row["setout_sequence"]
                if row["setout_sequence"] is not None
                else 999999,
                row["reporting_mark"].casefold(),
                row["number"].casefold(),
            )
        )

        return rows

    @staticmethod
    def get_pickup_rows(
        operations_session_id,
    ):
        """
        Return switch-list rows grouped for pickup work.

        A pickup is represented by a Waybill whose origin
        identifies a specific Industry/Track/Spot.

        General railroad origins such as Staging Yard or
        Interchange are not treated as physical industry
        pickups.
        """

        rows = (
            SwitchListService.get_switch_list_rows(
                operations_session_id
            )
        )

        pickup_rows = []

        for row in rows:

            if (
                row["origin_industry"]
                and row["origin_track"]
                and row["origin_spot"]
            ):

                pickup_rows.append(
                    row
                )

        pickup_rows.sort(
            key=lambda row: (
                (row["train"] or "Unassigned").casefold(),
                row["pickup_sequence"]
                if row["pickup_sequence"] is not None
                else 999999,
                row["origin_industry"].casefold(),
                row["origin_track"].casefold(),
                int(row["origin_spot"])
                if row["origin_spot"].isdigit()
                else 0,
                row["reporting_mark"].casefold(),
                row["number"].casefold(),
            )
        )

        return pickup_rows

    @staticmethod
    def get_setout_rows(
        operations_session_id,
    ):
        """
        Return switch-list rows grouped for set-out work.

        Set-outs are ordered by destination Industry,
        Track, Spot, and then car.
        """

        rows = (
            SwitchListService.get_switch_list_rows(
                operations_session_id
            )
        )

        rows.sort(
            key=lambda row: (
                (row["train"] or "Unassigned").casefold(),
                row["setout_sequence"]
                if row["setout_sequence"] is not None
                else 999999,
                row["destination_industry"].casefold(),
                row["destination_track"].casefold(),
                int(row["destination_spot"])
                if row["destination_spot"].isdigit()
                else 0,
                row["reporting_mark"].casefold(),
                row["number"].casefold(),
            )
        )

        return rows
