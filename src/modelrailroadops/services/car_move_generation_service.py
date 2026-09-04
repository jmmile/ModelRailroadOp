from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.location import Location
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.waybill import Waybill

from modelrailroadops.services.car_move_service import (
    CarMoveService,
)

from modelrailroadops.services.operations_session_train_service import (
    OperationsSessionTrainService,
)

from modelrailroadops.services.train_route_service import (
    TrainRouteService,
)


class CarMoveGenerationService:
    """
    Service used to generate CarMove records from the
    Waybills and Trains assigned to an Operations Session.

    Generation uses the following process:

        Operations Session
            -> Assigned Trains
            -> Train Routes
            -> Active Waybills
            -> Matching Train
            -> PICKUP CarMove
            -> SETOUT CarMove

    A train can handle a Waybill when its route contains
    both the Waybill origin location and destination
    location, with the origin occurring before the
    destination.

    Route stops and Waybills are matched primarily by
    structured Location identity when available.

    A TrainRoute stop represents service to the entire
    railroad Location. The specific LocationTrack selected
    by a Waybill determines the actual pickup or setout
    track and does not restrict route matching.

    Industry identity and normalized location text remain
    as fallbacks for legacy data.

    Existing CarMoves for the same Operations Session
    and Waybill are not duplicated.
    """

    #
    # Normalize location text.
    #

    @staticmethod
    def normalize_location(
        value,
    ):

        if value is None:

            return ""

        return str(
            value
        ).strip().casefold()

    #
    # Get Operations Session.
    #

    @staticmethod
    def get_operations_session(
        operations_session_id,
    ):

        if operations_session_id is None:

            return None

        with SessionLocal() as session:

            return session.get(
                OperationsSession,
                operations_session_id,
            )

    #
    # Get Waybills for an Operations Session.
    #
    # Only unfinished Waybills are candidates for
    # CarMove generation.
    #

    @staticmethod
    def get_waybills_for_session(
        operations_session_id,
    ):

        if operations_session_id is None:

            return []

        with SessionLocal() as session:

            statement = (
                select(
                    Waybill
                )
                .where(
                    Waybill.operations_session_id
                    == operations_session_id,
                    Waybill.status.in_(
                        [
                            "ACTIVE",
                            "IN_PROGRESS",
                        ]
                    ),
                )
                .order_by(
                    Waybill.created_at,
                    Waybill.id,
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
    # Get Industry name.
    #
    # Waybill objects returned by
    # get_waybills_for_session() are detached after
    # the database session closes.
    #
    # Therefore, do not access:
    #
    #     waybill.destination_industry
    #
    # or:
    #
    #     waybill.origin_industry
    #
    # because SQLAlchemy may attempt a lazy load on
    # a detached object.
    #
    # Instead, use the Industry ID and explicitly
    # load the Industry.
    #

    @staticmethod
    def get_industry_name(
        industry_id,
    ):

        if industry_id is None:

            return ""

        with SessionLocal() as session:

            industry = session.get(
                Industry,
                industry_id,
            )

            if industry is None:

                return ""

            return (
                industry.name
                or ""
            )

    @staticmethod
    def get_location_name(
        location_id,
    ):

        if location_id is None:

            return ""

        with SessionLocal() as session:

            location = session.get(
                Location,
                location_id,
            )

            return (
                location.name
                if location is not None
                else ""
            )

    #
    # Get destination location.
    #
    # The destination may be an Industry or a general
    # railroad location.
    #

    @staticmethod
    def get_destination_location(
        waybill,
    ):

        if waybill is None:

            return ""

        destination_industry_id = (
            getattr(
                waybill,
                "destination_industry_id",
                None,
            )
        )

        if destination_industry_id is not None:

            industry_name = (
                CarMoveGenerationService.get_industry_name(
                    destination_industry_id
                )
            )

            if industry_name:

                return industry_name

        destination_location_id = getattr(
            waybill,
            "destination_location_id",
            None,
        )

        if destination_location_id is not None:

            location_name = (
                CarMoveGenerationService.get_location_name(
                    destination_location_id
                )
            )

            if location_name:

                return location_name

        return (
            getattr(
                waybill,
                "destination_location",
                None,
            )
            or ""
        )

    #
    # Get origin location.
    #
    # The origin may be an Industry or a general
    # railroad location.
    #

    @staticmethod
    def get_origin_location(
        waybill,
    ):

        if waybill is None:

            return ""

        origin_industry_id = (
            getattr(
                waybill,
                "origin_industry_id",
                None,
            )
        )

        if origin_industry_id is not None:

            industry_name = (
                CarMoveGenerationService.get_industry_name(
                    origin_industry_id
                )
            )

            if industry_name:

                return industry_name

        origin_location_id = getattr(
            waybill,
            "origin_location_id",
            None,
        )

        if origin_location_id is not None:

            location_name = (
                CarMoveGenerationService.get_location_name(
                    origin_location_id
                )
            )

            if location_name:

                return location_name

        return (
            getattr(
                waybill,
                "origin_location",
                None,
            )
            or ""
        )

    #
    # Get car.
    #

    @staticmethod
    def get_car(
        car_id,
    ):

        if car_id is None:

            return None

        with SessionLocal() as session:

            return session.get(
                Car,
                car_id,
            )

    #
    # Determine whether a TrainRoute matches
    # a Waybill location.
    #
    # Structured Location identity takes precedence.
    #
    # A TrainRoute stop represents service to the entire
    # Location. Therefore, when the route and Waybill have
    # matching Location IDs, the route matches regardless
    # of which LocationTrack the Waybill uses.
    #
    # This allows one train stop at a location such as
    # Devin Fuel Distributors to serve multiple tracks,
    # such as Fuel Loading and Propane Loading.
    #
    # Industry identity and normalized location text remain
    # as fallbacks for legacy data.
    #

    @staticmethod
    def route_matches_location(
        route,
        industry_id,
        location,
        location_id=None,
        location_track_id=None,
    ):

        if route is None:

            return False

        #
        # Structured Location identity takes precedence.
        #
        # If both the TrainRoute and Waybill identify the
        # same Location, the route serves that Location.
        #
        # The Waybill's LocationTrack is intentionally not
        # used to restrict route matching.
        #

        if location_id is not None:

            route_location_id = getattr(
                route,
                "location_id",
                None,
            )

            if route_location_id is not None:

                return (
                    route_location_id
                    == location_id
                )

        #
        # Fall back to Industry identity for older route
        # and Waybill data.
        #

        if industry_id is not None:

            route_industry_id = (
                getattr(
                    route,
                    "industry_id",
                    None,
                )
            )

            return (
                route_industry_id
                == industry_id
            )

        #
        # Fall back to normalized location text for
        # legacy data.
        #

        normalized_location = (
            CarMoveGenerationService.normalize_location(
                location
            )
        )

        if not normalized_location:

            return False

        route_location = (
            CarMoveGenerationService.normalize_location(
                getattr(
                    route,
                    "location",
                    None,
                )
            )
        )

        return (
            route_location
            == normalized_location
        )

    #
    # Find the first route sequence matching
    # a Waybill location.
    #

    @staticmethod
    def find_route_sequence(
        routes,
        industry_id,
        location,
        location_id=None,
        location_track_id=None,
    ):

        if not routes:

            return None

        for route in routes:

            if (
                CarMoveGenerationService.route_matches_location(
                    route,
                    industry_id,
                    location,
                    location_id,
                    location_track_id,
                )
            ):

                return route.sequence

        return None

    #
    # Find a matching train.
    #
    # The first assigned train whose route contains
    # the origin before the destination is selected.
    #
    # Structured Location IDs are used when available.
    # LocationTrack IDs do not restrict route matching.
    #
    # Industry IDs and location text support legacy data.
    #

    @staticmethod
    def find_matching_train(
        assignments,
        waybill,
    ):

        if not assignments:

            return (
                None,
                None,
                None,
                None,
                (
                    "No trains are assigned to this "
                    "Operations Session."
                ),
            )

        if waybill is None:

            return (
                None,
                None,
                None,
                None,
                "Waybill was not found.",
            )

        origin_industry_id = (
            getattr(
                waybill,
                "origin_industry_id",
                None,
            )
        )

        destination_industry_id = (
            getattr(
                waybill,
                "destination_industry_id",
                None,
            )
        )

        origin_location_id = getattr(
            waybill,
            "origin_location_id",
            None,
        )

        origin_location_track_id = getattr(
            waybill,
            "origin_location_track_id",
            None,
        )

        destination_location_id = getattr(
            waybill,
            "destination_location_id",
            None,
        )

        destination_location_track_id = getattr(
            waybill,
            "destination_location_track_id",
            None,
        )

        origin_location = (
            CarMoveGenerationService.get_origin_location(
                waybill
            )
        )

        destination_location = (
            CarMoveGenerationService.get_destination_location(
                waybill
            )
        )

        if (
            origin_industry_id is None
            and not origin_location
        ):

            return (
                None,
                None,
                None,
                None,
                "Waybill has no origin location.",
            )

        if (
            destination_industry_id is None
            and not destination_location
        ):

            return (
                None,
                None,
                None,
                None,
                (
                    "Waybill has no destination "
                    "location."
                ),
            )

        for assignment in assignments:

            train_id = (
                getattr(
                    assignment,
                    "train_id",
                    None,
                )
            )

            if train_id is None:

                continue

            routes = (
                TrainRouteService.get_by_train(
                    train_id
                )
            )

            if not routes:

                continue

            origin_sequence = (
                CarMoveGenerationService.find_route_sequence(
                    routes,
                    origin_industry_id,
                    origin_location,
                    origin_location_id,
                    origin_location_track_id,
                )
            )

            destination_sequence = (
                CarMoveGenerationService.find_route_sequence(
                    routes,
                    destination_industry_id,
                    destination_location,
                    destination_location_id,
                    destination_location_track_id,
                )
            )

            if (
                origin_sequence is None
                or destination_sequence is None
            ):

                continue

            if (
                origin_sequence
                >= destination_sequence
            ):

                continue

            return (
                assignment,
                routes,
                origin_sequence,
                destination_sequence,
                "",
            )

        return (
            None,
            None,
            None,
            None,
            (
                f"No assigned train has a route from "
                f"'{origin_location}' "
                f"to "
                f"'{destination_location}'."
            ),
        )

    #
    # Determine whether this Waybill already has
    # CarMoves in this Operations Session.
    #

    @staticmethod
    def waybill_has_moves(
        existing_moves,
        waybill_id,
    ):

        for move in existing_moves:

            if (
                move.waybill_id
                == waybill_id
            ):

                return True

        return False

    #
    # Generate CarMoves for an Operations Session.
    #

    @staticmethod
    def generate(
        operations_session_id,
    ):

        if operations_session_id is None:

            return (
                False,
                {
                    "generated": 0,
                    "skipped": 0,
                    "messages": [
                        "Operations Session is required."
                    ],
                },
            )

        operations_session = (
            CarMoveGenerationService.get_operations_session(
                operations_session_id
            )
        )

        if operations_session is None:

            return (
                False,
                {
                    "generated": 0,
                    "skipped": 0,
                    "messages": [
                        "Operations Session not found."
                    ],
                },
            )

        status = (
            getattr(
                operations_session,
                "status",
                None,
            )
        )

        if status == "COMPLETED":

            return (
                False,
                {
                    "generated": 0,
                    "skipped": 0,
                    "messages": [
                        (
                            "Car Moves cannot be generated "
                            "for a completed Operations Session."
                        )
                    ],
                },
            )

        if status == "CANCELLED":

            return (
                False,
                {
                    "generated": 0,
                    "skipped": 0,
                    "messages": [
                        (
                            "Car Moves cannot be generated "
                            "for a cancelled Operations Session."
                        )
                    ],
                },
            )

        assignments = (
            OperationsSessionTrainService.get_by_operations_session(
                operations_session_id
            )
        )

        waybills = (
            CarMoveGenerationService.get_waybills_for_session(
                operations_session_id
            )
        )

        existing_moves = (
            CarMoveService.get_by_operations_session(
                operations_session_id
            )
        )

        generated = 0

        skipped = 0

        messages = []

        for waybill in waybills:

            #
            # Do not generate duplicate moves.
            #

            if (
                CarMoveGenerationService.waybill_has_moves(
                    existing_moves,
                    waybill.id,
                )
            ):

                skipped += 1

                messages.append(
                    (
                        f"Waybill #{waybill.id} "
                        "already has Car Moves."
                    )
                )

                continue

            car = (
                CarMoveGenerationService.get_car(
                    waybill.car_id
                )
            )

            if car is None:

                skipped += 1

                messages.append(
                    (
                        f"Waybill #{waybill.id}: "
                        "assigned car was not found."
                    )
                )

                continue

            match = (
                CarMoveGenerationService.find_matching_train(
                    assignments,
                    waybill,
                )
            )

            (
                assignment,
                routes,
                origin_sequence,
                destination_sequence,
                message,
            ) = match

            if assignment is None:

                skipped += 1

                messages.append(
                    (
                        f"Waybill #{waybill.id}: "
                        f"{message}"
                    )
                )

                continue

            train_id = (
                assignment.train_id
            )

            origin_location = (
                CarMoveGenerationService.get_origin_location(
                    waybill
                )
            )

            destination_location = (
                CarMoveGenerationService.get_destination_location(
                    waybill
                )
            )

            car_display = (
                f"{car.reporting_mark} "
                f"{car.number}"
            )

            #
            # Create PICKUP.
            #
            # The pickup occurs at the Waybill origin
            # route sequence.
            #

            success, result = (
                CarMoveService.create(
                    operations_session_id=(
                        operations_session_id
                    ),
                    train_id=train_id,
                    car_id=waybill.car_id,
                    waybill_id=waybill.id,
                    move_type="PICKUP",
                    route_sequence=origin_sequence,
                    origin_location=(
                        origin_location
                    ),
                    destination_location=(
                        destination_location
                    ),
                    notes=(
                        f"Pickup for Waybill "
                        f"#{waybill.id} - "
                        f"{car_display}"
                    ),
                )
            )

            if not success:

                skipped += 1

                messages.append(
                    (
                        f"Waybill #{waybill.id}: "
                        f"Could not create PICKUP move: "
                        f"{result}"
                    )
                )

                continue

            pickup_move = result

            generated += 1

            existing_moves.append(
                pickup_move
            )

            #
            # Create SETOUT.
            #
            # The setout occurs at the Waybill
            # destination route sequence.
            #

            success, result = (
                CarMoveService.create(
                    operations_session_id=(
                        operations_session_id
                    ),
                    train_id=train_id,
                    car_id=waybill.car_id,
                    waybill_id=waybill.id,
                    move_type="SETOUT",
                    route_sequence=destination_sequence,
                    origin_location=(
                        origin_location
                    ),
                    destination_location=(
                        destination_location
                    ),
                    notes=(
                        f"Setout for Waybill "
                        f"#{waybill.id} - "
                        f"{car_display}"
                    ),
                )
            )

            if not success:

                #
                # The PICKUP was already created.
                # Remove it so a partially generated
                # Waybill does not remain.
                #

                CarMoveService.delete(
                    getattr(
                        pickup_move,
                        "id",
                        None,
                    )
                )

                if pickup_move in existing_moves:

                    existing_moves.remove(
                        pickup_move
                    )

                generated -= 1

                skipped += 1

                messages.append(
                    (
                        f"Waybill #{waybill.id}: "
                        f"Could not create SETOUT move: "
                        f"{result}"
                    )
                )

                continue

            generated += 1

            existing_moves.append(
                result
            )

            messages.append(
                (
                    f"Waybill #{waybill.id}: "
                    f"generated PICKUP and SETOUT "
                    f"for train {train_id}."
                )
            )

        return (
            True,
            {
                "generated": generated,
                "skipped": skipped,
                "messages": messages,
            },
        )

    #
    # Generate CarMoves and return a simple summary.
    #

    @staticmethod
    def generate_summary(
        operations_session_id,
    ):

        success, result = (
            CarMoveGenerationService.generate(
                operations_session_id
            )
        )

        if not success:

            return (
                False,
                result,
            )

        generated = (
            result.get(
                "generated",
                0,
            )
        )

        skipped = (
            result.get(
                "skipped",
                0,
            )
        )

        return (
            True,
            (
                f"Generated {generated} Car Move(s). "
                f"Skipped {skipped} Waybill(s)."
            ),
        )