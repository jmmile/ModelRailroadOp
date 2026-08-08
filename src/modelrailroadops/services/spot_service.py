#```python
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.spot import Spot
from modelrailroadops.models.car import Car


class SpotService:
    """
    Service methods for managing track spots.
    """

    @staticmethod
    def get_by_track(track_id):
        """
        Return all spots belonging to an industry track.
        """

        with SessionLocal() as session:

            return (
                session.execute(
                    select(Spot)
                    .options(
                        joinedload(Spot.car)
                    )
                    .where(
                        Spot.track_id == track_id
                    )
                    .order_by(
                        Spot.spot_number
                    )
                )
                .scalars()
                .unique()
                .all()
            )

    @staticmethod
    def add(
        track_id,
        spot_number,
        name=None,
        description=None,
        max_length=None,
        allowed_car_type=None,
        allowed_owner=None,
        hazardous_allowed=True,
        load_only=False,
        empty_only=False,
        notes=None,
    ):
        """
        Add a new spot to an industry track.
        """

        with SessionLocal() as session:

            existing = (
                session.execute(
                    select(Spot)
                    .where(
                        Spot.track_id == track_id,
                        Spot.spot_number == spot_number,
                    )
                )
                .scalars()
                .first()
            )

            if existing:
                return existing

            spot = Spot(
                track_id=track_id,
                spot_number=spot_number,
                name=name,
                description=description,
                max_length=max_length,
                allowed_car_type=allowed_car_type,
                allowed_owner=allowed_owner,
                hazardous_allowed=hazardous_allowed,
                load_only=load_only,
                empty_only=empty_only,
                notes=notes,
            )

            session.add(spot)

            session.commit()

            session.refresh(spot)

            return spot

    @staticmethod
    def update(
        spot_id,
        name=None,
        description=None,
        max_length=None,
        allowed_car_type=None,
        allowed_owner=None,
        hazardous_allowed=True,
        load_only=False,
        empty_only=False,
        notes=None,
    ):
        """
        Update an existing spot.
        """

        with SessionLocal() as session:

            spot = session.get(
                Spot,
                spot_id
            )

            if spot is None:
                return None

            spot.name = name
            spot.description = description
            spot.max_length = max_length
            spot.allowed_car_type = allowed_car_type
            spot.allowed_owner = allowed_owner
            spot.hazardous_allowed = hazardous_allowed
            spot.load_only = load_only
            spot.empty_only = empty_only
            spot.notes = notes

            session.commit()

            session.refresh(spot)

            return spot

    @staticmethod
    def check_restriction_violation(
        spot_id
    ):
        """
        Check whether the car currently occupying a spot
        violates the spot's restrictions.

        Returns:
            (True, "") when there is no violation.
            (False, "message") when a violation exists.
        """

        with SessionLocal() as session:

            spot = (
                session.execute(
                    select(Spot)
                    .options(
                        joinedload(Spot.car)
                    )
                    .where(
                        Spot.id == spot_id
                    )
                )
                .scalars()
                .unique()
                .one_or_none()
            )

            if spot is None:

                return (
                    False,
                    "Spot not found."
                )

            car = spot.car

            if car is None:

                return (
                    True,
                    ""
                )

            errors = []

            #
            # Car type
            #

            if spot.allowed_car_type:

                if car.car_type != spot.allowed_car_type:

                    errors.append(
                        (
                            f"Car type mismatch: "
                            f"{car.car_type} "
                            f"(requires "
                            f"{spot.allowed_car_type})"
                        )
                    )

            #
            # Owner
            #

            if spot.allowed_owner:

                if car.owner != spot.allowed_owner:

                    errors.append(
                        (
                            f"Owner mismatch: "
                            f"{car.owner} "
                            f"(requires "
                            f"{spot.allowed_owner})"
                        )
                    )

            #
            # Length
            #

            if (
                spot.max_length is not None
                and car.length is not None
            ):

                if car.length > spot.max_length:

                    errors.append(
                        (
                            f"Length exceeds limit: "
                            f"{car.length} ft "
                            f"(maximum "
                            f"{spot.max_length} ft)"
                        )
                    )

            #
            # Restrictions
            #

            # Note:
            # Loaded/empty and hazardous restrictions
            # can be expanded here when the Car model has
            # the corresponding load/hazard fields.

            if not errors:

                return (
                    True,
                    ""
                )

            return (
                False,
                "\n".join(errors)
            )

    @staticmethod
    def is_occupied(
        spot_id
    ):
        """
        Return True if a car currently occupies the spot.
        """

        with SessionLocal() as session:

            car = (
                session.execute(
                    select(Car)
                    .where(
                        Car.spot_id == spot_id
                    )
                )
                .scalars()
                .first()
            )

            return car is not None

    @staticmethod
    def delete(
        spot_id
    ):
        """
        Delete a spot.

        An occupied spot can NEVER be deleted.
        """

        with SessionLocal() as session:

            spot = session.get(
                Spot,
                spot_id
            )

            if spot is None:

                return False

            #
            # IMPORTANT:
            #
            # Check the Car table directly instead of relying
            # on spot.car. This prevents lazy-loading/session
            # problems and guarantees that an occupied spot
            # cannot be deleted.
            #

            car = (
                session.execute(
                    select(Car)
                    .where(
                        Car.spot_id == spot_id
                    )
                )
                .scalars()
                .first()
            )

            if car is not None:

                return False

            session.delete(
                spot
            )

            session.commit()

            return True
#```
