from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.train import Train


class TrainService:
    """
    Service for creating, retrieving, updating,
    and deleting Train records.
    """

    #
    # Get all trains
    #

    @staticmethod
    def get_all(
        include_inactive=True,
    ):

        with SessionLocal() as session:

            statement = (
                select(
                    Train
                )
            )

            if not include_inactive:

                statement = statement.where(
                    Train.active.is_(True)
                )

            statement = statement.order_by(
                Train.number,
                Train.name,
            )

            return (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

    #
    # Get train by ID
    #

    @staticmethod
    def get_by_id(
        train_id,
    ):

        if train_id is None:

            return None

        with SessionLocal() as session:

            return session.get(
                Train,
                train_id,
            )

    #
    # Get train by number
    #

    @staticmethod
    def get_by_number(
        number,
    ):

        if not number:

            return None

        with SessionLocal() as session:

            statement = (
                select(
                    Train
                )
                .where(
                    Train.number
                    == number.strip()
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
    # Create train
    #

    @staticmethod
    def create(
        name,
        number,
        description=None,
        origin=None,
        destination=None,
        direction=None,
        active=True,
        train_type=None,
        priority=None,
        maximum_cars=None,
        maximum_tonnage=None,
        operating_days=None,
        scheduled_departure=None,
        scheduled_arrival=None,
    ):

        name = (
            name.strip()
            if name
            else ""
        )

        number = (
            number.strip()
            if number
            else ""
        )

        if not name:

            return (
                False,
                "Train name is required.",
            )

        if not number:

            return (
                False,
                "Train number is required.",
            )

        if (
            maximum_cars is not None
            and maximum_cars <= 0
        ):

            return (
                False,
                "Maximum cars must be greater than zero.",
            )

        if (
            maximum_tonnage is not None
            and maximum_tonnage <= 0
        ):

            return (
                False,
                "Maximum tonnage must be greater than zero.",
            )

        with SessionLocal() as session:

            existing_train = (
                session.execute(
                    select(
                        Train
                    ).where(
                        Train.number
                        == number
                    )
                )
                .scalars()
                .first()
            )

            if existing_train is not None:

                return (
                    False,
                    (
                        f"Train number "
                        f"'{number}' already exists."
                    ),
                )

            train = Train(
                name=name,
                number=number,
                description=(
                    description.strip()
                    if description
                    else None
                ),
                origin=(
                    origin.strip()
                    if origin
                    else None
                ),
                destination=(
                    destination.strip()
                    if destination
                    else None
                ),
                direction=(
                    direction.strip()
                    if direction
                    else None
                ),
                train_type=(
                    train_type.strip()
                    if train_type
                    else None
                ),
                priority=priority,
                maximum_cars=maximum_cars,
                maximum_tonnage=maximum_tonnage,
                operating_days=(
                    operating_days.strip()
                    if operating_days
                    else None
                ),
                scheduled_departure=scheduled_departure,
                scheduled_arrival=scheduled_arrival,
                active=bool(
                    active
                ),
            )

            session.add(
                train
            )

            session.commit()

            session.refresh(
                train
            )

            return (
                True,
                train,
            )

    #
    # Update train
    #

    @staticmethod
    def update(
        train_id,
        name,
        number,
        description=None,
        origin=None,
        destination=None,
        direction=None,
        active=True,
        train_type=None,
        priority=None,
        maximum_cars=None,
        maximum_tonnage=None,
        operating_days=None,
        scheduled_departure=None,
        scheduled_arrival=None,
    ):

        if train_id is None:

            return (
                False,
                "No train was specified.",
            )

        name = (
            name.strip()
            if name
            else ""
        )

        number = (
            number.strip()
            if number
            else ""
        )

        if not name:

            return (
                False,
                "Train name is required.",
            )

        if not number:

            return (
                False,
                "Train number is required.",
            )

        if (
            maximum_cars is not None
            and maximum_cars <= 0
        ):

            return (
                False,
                "Maximum cars must be greater than zero.",
            )

        if (
            maximum_tonnage is not None
            and maximum_tonnage <= 0
        ):

            return (
                False,
                "Maximum tonnage must be greater than zero.",
            )

        with SessionLocal() as session:

            train = session.get(
                Train,
                train_id,
            )

            if train is None:

                return (
                    False,
                    (
                        f"Train {train_id} "
                        "was not found."
                    ),
                )

            existing_train = (
                session.execute(
                    select(
                        Train
                    ).where(
                        Train.number
                        == number,
                        Train.id
                        != train_id,
                    )
                )
                .scalars()
                .first()
            )

            if existing_train is not None:

                return (
                    False,
                    (
                        f"Train number "
                        f"'{number}' already exists."
                    ),
                )

            train.name = name

            train.number = number

            train.description = (
                description.strip()
                if description
                else None
            )

            train.origin = (
                origin.strip()
                if origin
                else None
            )

            train.destination = (
                destination.strip()
                if destination
                else None
            )

            train.direction = (
                direction.strip()
                if direction
                else None
            )

            train.train_type = (
                train_type.strip()
                if train_type
                else None
            )

            train.priority = priority

            train.maximum_cars = maximum_cars

            train.maximum_tonnage = maximum_tonnage

            train.operating_days = (
                operating_days.strip()
                if operating_days
                else None
            )

            train.scheduled_departure = scheduled_departure

            train.scheduled_arrival = scheduled_arrival

            train.active = bool(
                active
            )

            session.commit()

            session.refresh(
                train
            )

            return (
                True,
                train,
            )

    #
    # Activate train
    #

    @staticmethod
    def activate(
        train_id,
    ):

        return TrainService.set_active(
            train_id,
            True,
        )

    #
    # Deactivate train
    #

    @staticmethod
    def deactivate(
        train_id,
    ):

        return TrainService.set_active(
            train_id,
            False,
        )

    #
    # Set active status
    #

    @staticmethod
    def set_active(
        train_id,
        active,
    ):

        if train_id is None:

            return (
                False,
                "No train was specified.",
            )

        with SessionLocal() as session:

            train = session.get(
                Train,
                train_id,
            )

            if train is None:

                return (
                    False,
                    "Train "
                    f"{train_id} "
                    "was not found.",
                )

            train.active = bool(
                active
            )

            session.commit()

            session.refresh(
                train
            )

            return (
                True,
                train,
            )

    #
    # Delete train
    #

    @staticmethod
    def delete(
        train_id,
    ):

        if train_id is None:

            return (
                False,
                "No train was specified.",
            )

        with SessionLocal() as session:

            train = session.get(
                Train,
                train_id,
            )

            if train is None:

                return (
                    False,
                    (
                        f"Train {train_id} "
                        "was not found."
                    ),
                )

            session.delete(
                train
            )

            session.commit()

            return (
                True,
                "Train deleted successfully.",
            )