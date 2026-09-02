from sqlalchemy import (
    select,
)
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.industry import Industry
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.train import Train
from modelrailroadops.models.train_route import TrainRoute


class TrainRouteService:
    """
    Service for creating, retrieving, updating,
    deleting, and reordering TrainRoute records.
    """

    @staticmethod
    def _sync_train_endpoints(
        session,
        train_id,
    ):
        """Derive Train origin/destination from its ordered route."""

        train = session.get(
            Train,
            train_id,
        )

        if train is None:

            return

        routes = (
            session.execute(
                select(
                    TrainRoute
                )
                .where(
                    TrainRoute.train_id
                    == train_id
                )
                .options(
                    selectinload(TrainRoute.operating_location),
                    selectinload(TrainRoute.operating_track),
                )
                .order_by(
                    TrainRoute.sequence,
                    TrainRoute.id,
                )
            )
            .scalars()
            .all()
        )

        train.origin = routes[0].location if routes else None
        train.destination = routes[-1].location if routes else None

    @staticmethod
    def _get_or_create_location(
        session,
        location,
        industry_id=None,
    ):

        if industry_id is not None:

            industry = session.get(
                Industry,
                industry_id,
            )

            if (
                industry is not None
                and industry.operating_location_id is not None
            ):

                return industry.operating_location_id

        operating_location = (
            session.execute(
                select(Location).where(
                    Location.name == location
                )
            )
            .scalars()
            .first()
        )

        if operating_location is None:

            lower_name = location.lower()

            if "staging" in lower_name:
                location_type = "STAGING"
            elif "interchange" in lower_name:
                location_type = "INTERCHANGE"
            elif "yard" in lower_name:
                location_type = "YARD"
            else:
                location_type = "OTHER"

            operating_location = Location(
                name=location,
                location_type=location_type,
                active=True,
            )

            session.add(
                operating_location
            )

            session.flush()

        return operating_location.id

    @staticmethod
    def _resolve_route_location(
        session,
        location,
        location_id=None,
        location_track_id=None,
        industry_id=None,
    ):

        if location_id is None:

            location_id = TrainRouteService._get_or_create_location(
                session,
                location,
                industry_id,
            )

        operating_location = session.get(
            Location,
            location_id,
        )

        if operating_location is None:
            raise ValueError("Route location was not found.")

        location = operating_location.name

        linked_industry = (
            session.execute(
                select(Industry).where(
                    Industry.operating_location_id == location_id
                )
            )
            .scalars()
            .first()
        )

        industry_id = (
            linked_industry.id
            if linked_industry is not None
            else None
        )

        if location_track_id is not None:

            operating_track = session.get(
                LocationTrack,
                location_track_id,
            )

            if (
                operating_track is None
                or operating_track.location_id != location_id
            ):
                raise ValueError(
                    "The selected track does not belong to the route location."
                )

        return (
            location,
            location_id,
            location_track_id,
            industry_id,
        )

    #
    # Get all route stops for a train
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
                    TrainRoute
                )
                .options(
                    selectinload(TrainRoute.operating_location),
                    selectinload(TrainRoute.operating_track),
                )
                .where(
                    TrainRoute.train_id
                    == train_id
                )
                .order_by(
                    TrainRoute.sequence,
                    TrainRoute.id,
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
    # Get route stop by ID
    #

    @staticmethod
    def get_by_id(
        route_id,
    ):

        if route_id is None:

            return None

        with SessionLocal() as session:

            return (
                session.execute(
                    select(TrainRoute)
                    .options(
                        selectinload(TrainRoute.operating_location),
                        selectinload(TrainRoute.operating_track),
                    )
                    .where(TrainRoute.id == route_id)
                )
                .scalars()
                .first()
            )

    #
    # Get next sequence number
    #

    @staticmethod
    def get_next_sequence(
        train_id,
    ):

        routes = (
            TrainRouteService.get_by_train(
                train_id
            )
        )

        if not routes:

            return 1

        return (
            max(
                route.sequence
                for route in routes
            )
            + 1
        )

    @staticmethod
    def set_endpoints(
        train_id,
        origin_location_id,
        origin_track_id,
        destination_location_id,
        destination_track_id,
    ):
        """Create or update the first and last route stops atomically.

        Intermediate stops are preserved. A route with no stops receives two
        stops; a one-stop route keeps that stop as its origin and receives a
        new destination.
        """

        if train_id is None:
            return False, "No train was specified."

        if origin_location_id is None or origin_track_id is None:
            return False, "Origin Location and Track are required."

        if destination_location_id is None or destination_track_id is None:
            return False, "Destination Location and Track are required."

        with SessionLocal() as session:
            train = session.get(Train, train_id)

            if train is None:
                return False, "Train was not found."

            try:
                origin_values = TrainRouteService._resolve_route_location(
                    session,
                    "",
                    origin_location_id,
                    origin_track_id,
                )
                destination_values = TrainRouteService._resolve_route_location(
                    session,
                    "",
                    destination_location_id,
                    destination_track_id,
                )
            except ValueError as exc:
                return False, str(exc)

            routes = (
                session.execute(
                    select(TrainRoute)
                    .where(TrainRoute.train_id == train_id)
                    .order_by(TrainRoute.sequence, TrainRoute.id)
                )
                .scalars()
                .all()
            )

            def apply_endpoint(route, values):
                (
                    route.location,
                    route.location_id,
                    route.location_track_id,
                    route.industry_id,
                ) = values

            if not routes:
                origin_route = TrainRoute(train_id=train_id, sequence=1)
                destination_route = TrainRoute(train_id=train_id, sequence=2)
                apply_endpoint(origin_route, origin_values)
                apply_endpoint(destination_route, destination_values)
                session.add_all([origin_route, destination_route])
            elif len(routes) == 1:
                apply_endpoint(routes[0], origin_values)
                destination_route = TrainRoute(
                    train_id=train_id,
                    sequence=routes[0].sequence + 1,
                )
                apply_endpoint(destination_route, destination_values)
                session.add(destination_route)
            else:
                apply_endpoint(routes[0], origin_values)
                apply_endpoint(routes[-1], destination_values)

            session.flush()
            TrainRouteService._sync_train_endpoints(session, train_id)
            session.commit()

            return True, "Train route endpoints updated."

    #
    # Validate industry
    #

    @staticmethod
    def get_industry(
        industry_id,
    ):

        if industry_id is None:

            return None

        with SessionLocal() as session:

            return session.get(
                Industry,
                industry_id,
            )

    #
    # Create route stop
    #

    @staticmethod
    def create(
        train_id,
        location,
        sequence=None,
        description=None,
        industry_id=None,
        location_id=None,
        location_track_id=None,
    ):

        if train_id is None:

            return (
                False,
                "No train was specified.",
            )

        location = (
            location.strip()
            if location
            else ""
        )

        if not location:

            return (
                False,
                "Route location is required.",
            )

        #
        # Validate industry when supplied.
        #

        if industry_id is not None:

            industry = (
                TrainRouteService.get_industry(
                    industry_id
                )
            )

            if industry is None:

                return (
                    False,
                    (
                        f"Industry {industry_id} "
                        "was not found."
                    ),
                )

        if sequence is None:

            sequence = (
                TrainRouteService.get_next_sequence(
                    train_id
                )
            )

        try:

            sequence = int(
                sequence
            )

        except (
            TypeError,
            ValueError,
        ):

            return (
                False,
                "Route sequence must be a number.",
            )

        if sequence < 1:

            return (
                False,
                "Route sequence must be 1 or greater.",
            )

        with SessionLocal() as session:

            try:
                (
                    location,
                    location_id,
                    location_track_id,
                    industry_id,
                ) = TrainRouteService._resolve_route_location(
                    session,
                    location,
                    location_id,
                    location_track_id,
                    industry_id,
                )
            except ValueError as exc:
                return False, str(exc)

            #
            # Shift existing route stops when
            # inserting into an existing position.
            #

            existing_routes = (
                session.execute(
                    select(
                        TrainRoute
                    )
                    .where(
                        TrainRoute.train_id
                        == train_id,
                        TrainRoute.sequence
                        >= sequence,
                    )
                    .order_by(
                        TrainRoute.sequence.desc()
                    )
                )
                .scalars()
                .all()
            )

            for route in existing_routes:

                route.sequence += 1

            route = TrainRoute(
                train_id=train_id,
                industry_id=industry_id,
                location_id=location_id,
                location_track_id=location_track_id,
                sequence=sequence,
                location=location,
                description=(
                    description.strip()
                    if description
                    else None
                ),
            )

            session.add(
                route
            )

            session.flush()

            TrainRouteService._sync_train_endpoints(
                session,
                train_id,
            )

            session.commit()

            session.refresh(
                route
            )

            return (
                True,
                route,
            )

    #
    # Update route stop
    #

    @staticmethod
    def update(
        route_id,
        location,
        sequence,
        description=None,
        industry_id=None,
        location_id=None,
        location_track_id=None,
    ):

        if route_id is None:

            return (
                False,
                "No route stop was specified.",
            )

        location = (
            location.strip()
            if location
            else ""
        )

        if not location:

            return (
                False,
                "Route location is required.",
            )

        #
        # Validate industry when supplied.
        #

        if industry_id is not None:

            industry = (
                TrainRouteService.get_industry(
                    industry_id
                )
            )

            if industry is None:

                return (
                    False,
                    (
                        f"Industry {industry_id} "
                        "was not found."
                    ),
                )

        try:

            sequence = int(
                sequence
            )

        except (
            TypeError,
            ValueError,
        ):

            return (
                False,
                "Route sequence must be a number.",
            )

        if sequence < 1:

            return (
                False,
                "Route sequence must be 1 or greater.",
            )

        with SessionLocal() as session:

            route = session.get(
                TrainRoute,
                route_id,
            )

            if route is None:

                return (
                    False,
                    (
                        f"Route stop {route_id} "
                        "was not found."
                    ),
                )

            old_sequence = (
                route.sequence
            )

            train_id = (
                route.train_id
            )

            try:
                (
                    location,
                    location_id,
                    location_track_id,
                    industry_id,
                ) = TrainRouteService._resolve_route_location(
                    session,
                    location,
                    location_id,
                    location_track_id,
                    industry_id,
                )
            except ValueError as exc:
                return False, str(exc)

            if sequence != old_sequence:

                if sequence < old_sequence:

                    routes = (
                        session.execute(
                            select(
                                TrainRoute
                            )
                            .where(
                                TrainRoute.train_id
                                == train_id,
                                TrainRoute.sequence
                                >= sequence,
                                TrainRoute.sequence
                                < old_sequence,
                                TrainRoute.id
                                != route_id,
                            )
                            .order_by(
                                TrainRoute.sequence.desc()
                            )
                        )
                        .scalars()
                        .all()
                    )

                    for other_route in routes:

                        other_route.sequence += 1

                else:

                    routes = (
                        session.execute(
                            select(
                                TrainRoute
                            )
                            .where(
                                TrainRoute.train_id
                                == train_id,
                                TrainRoute.sequence
                                > old_sequence,
                                TrainRoute.sequence
                                <= sequence,
                                TrainRoute.id
                                != route_id,
                            )
                            .order_by(
                                TrainRoute.sequence
                            )
                        )
                        .scalars()
                        .all()
                    )

                    for other_route in routes:

                        other_route.sequence -= 1

            route.sequence = sequence

            route.location = location

            route.industry_id = industry_id

            route.location_id = location_id

            route.location_track_id = location_track_id

            route.description = (
                description.strip()
                if description
                else None
            )

            session.flush()

            TrainRouteService._sync_train_endpoints(
                session,
                train_id,
            )

            session.commit()

            session.refresh(
                route
            )

            return (
                True,
                route,
            )

    #
    # Move route stop up
    #

    @staticmethod
    def move_up(
        route_id,
    ):

        return TrainRouteService._move(
            route_id,
            -1,
        )

    #
    # Move route stop down
    #

    @staticmethod
    def move_down(
        route_id,
    ):

        return TrainRouteService._move(
            route_id,
            1,
        )

    #
    # Move route stop
    #

    @staticmethod
    def _move(
        route_id,
        direction,
    ):

        if route_id is None:

            return (
                False,
                "No route stop was specified.",
            )

        if direction not in (
            -1,
            1,
        ):

            return (
                False,
                "Invalid route movement.",
            )

        with SessionLocal() as session:

            route = session.get(
                TrainRoute,
                route_id,
            )

            if route is None:

                return (
                    False,
                    (
                        f"Route stop {route_id} "
                        "was not found."
                    ),
                )

            current_sequence = (
                route.sequence
            )

            target_sequence = (
                current_sequence
                + direction
            )

            if target_sequence < 1:

                return (
                    False,
                    "Route stop is already first.",
                )

            neighboring_route = (
                session.execute(
                    select(
                        TrainRoute
                    )
                    .where(
                        TrainRoute.train_id
                        == route.train_id,
                        TrainRoute.sequence
                        == target_sequence,
                    )
                )
                .scalars()
                .first()
            )

            if neighboring_route is None:

                if direction == 1:

                    return (
                        False,
                        "Route stop is already last.",
                    )

                return (
                    False,
                    "Route stop could not be moved.",
                )

            neighboring_route.sequence = (
                current_sequence
            )

            route.sequence = (
                target_sequence
            )

            session.flush()

            TrainRouteService._sync_train_endpoints(
                session,
                route.train_id,
            )

            session.commit()

            session.refresh(
                route
            )

            return (
                True,
                route,
            )

    #
    # Delete route stop
    #

    @staticmethod
    def delete(
        route_id,
    ):

        if route_id is None:

            return (
                False,
                "No route stop was specified.",
            )

        with SessionLocal() as session:

            route = session.get(
                TrainRoute,
                route_id,
            )

            if route is None:

                return (
                    False,
                    (
                        f"Route stop {route_id} "
                        "was not found."
                    ),
                )

            train_id = (
                route.train_id
            )

            deleted_sequence = (
                route.sequence
            )

            session.delete(
                route
            )

            #
            # Close the sequence gap created by
            # deleting this route stop.
            #

            routes = (
                session.execute(
                    select(
                        TrainRoute
                    )
                    .where(
                        TrainRoute.train_id
                        == train_id,
                        TrainRoute.sequence
                        > deleted_sequence,
                    )
                    .order_by(
                        TrainRoute.sequence
                    )
                )
                .scalars()
                .all()
            )

            for other_route in routes:

                other_route.sequence -= 1

            session.flush()

            TrainRouteService._sync_train_endpoints(
                session,
                train_id,
            )

            session.commit()

            return (
                True,
                "Route stop deleted successfully.",
            )

    #
    # Delete all route stops for a train
    #

    @staticmethod
    def delete_by_train(
        train_id,
    ):

        if train_id is None:

            return (
                False,
                "No train was specified.",
            )

        with SessionLocal() as session:

            routes = (
                session.execute(
                    select(
                        TrainRoute
                    )
                    .where(
                        TrainRoute.train_id
                        == train_id
                    )
                )
                .scalars()
                .all()
            )

            for route in routes:

                session.delete(
                    route
                )

            session.flush()

            TrainRouteService._sync_train_endpoints(
                session,
                train_id,
            )

            session.commit()

            return (
                True,
                (
                    f"Deleted {len(routes)} "
                    "route stop(s)."
                ),
            )
