from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car_movement import CarMovement


class CarMovementService:
    """
    Service for creating, retrieving, and deleting
    CarMovement records.
    """

    #
    # Get all car movements
    #

    @staticmethod
    def get_all():

        with SessionLocal() as session:

            statement = (
                select(
                    CarMovement
                )
                .order_by(
                    CarMovement.timestamp,
                    CarMovement.id,
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
    # Get movement by ID
    #

    @staticmethod
    def get_by_id(
        movement_id,
    ):

        if movement_id is None:

            return None

        with SessionLocal() as session:

            return session.get(
                CarMovement,
                movement_id,
            )

    #
    # Get movements for a car
    #

    @staticmethod
    def get_by_car(
        car_id,
    ):

        if car_id is None:

            return []

        with SessionLocal() as session:

            statement = (
                select(
                    CarMovement
                )
                .where(
                    CarMovement.car_id
                    == car_id
                )
                .order_by(
                    CarMovement.timestamp,
                    CarMovement.id,
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
    # Get movements for an Operations Session
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
                    CarMovement
                )
                .where(
                    CarMovement.operations_session_id
                    == operations_session_id
                )
                .order_by(
                    CarMovement.timestamp,
                    CarMovement.id,
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
    # Create car movement
    #

    @staticmethod
    def create(
        car_id,
        movement_type,
        from_location=None,
        to_location=None,
        operations_session_id=None,
        notes=None,
    ):

        if car_id is None:

            return (
                False,
                "No car was specified.",
            )

        movement_type = (
            movement_type.strip()
            if movement_type
            else ""
        )

        if not movement_type:

            return (
                False,
                "Movement type is required.",
            )

        from_location = (
            from_location.strip()
            if from_location
            else None
        )

        to_location = (
            to_location.strip()
            if to_location
            else None
        )

        notes = (
            notes.strip()
            if notes
            else None
        )

        with SessionLocal() as session:

            movement = CarMovement(
                car_id=car_id,
                operations_session_id=(
                    operations_session_id
                ),
                from_location=from_location,
                to_location=to_location,
                movement_type=movement_type,
                notes=notes,
            )

            session.add(
                movement
            )

            session.commit()

            session.refresh(
                movement
            )

            return (
                True,
                movement,
            )

    #
    # Delete movement
    #

    @staticmethod
    def delete(
        movement_id,
    ):

        if movement_id is None:

            return (
                False,
                "No car movement was specified.",
            )

        with SessionLocal() as session:

            movement = session.get(
                CarMovement,
                movement_id,
            )

            if movement is None:

                return (
                    False,
                    (
                        f"Car movement "
                        f"{movement_id} "
                        "was not found."
                    ),
                )

            session.delete(
                movement
            )

            session.commit()

            return (
                True,
                "Car movement deleted successfully.",
            )

    #
    # Delete all movements for an
    # Operations Session
    #

    @staticmethod
    def delete_by_operations_session(
        operations_session_id,
    ):

        if operations_session_id is None:

            return (
                False,
                "No Operations Session was specified.",
            )

        with SessionLocal() as session:

            statement = (
                select(
                    CarMovement
                )
                .where(
                    CarMovement.operations_session_id
                    == operations_session_id
                )
            )

            movements = (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

            for movement in movements:

                session.delete(
                    movement
                )

            session.commit()

            return (
                True,
                (
                    f"Deleted {len(movements)} "
                    "car movement(s)."
                ),
            )

    #
    # Delete all movements for a car
    #

    @staticmethod
    def delete_by_car(
        car_id,
    ):

        if car_id is None:

            return (
                False,
                "No car was specified.",
            )

        with SessionLocal() as session:

            statement = (
                select(
                    CarMovement
                )
                .where(
                    CarMovement.car_id
                    == car_id
                )
            )

            movements = (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

            for movement in movements:

                session.delete(
                    movement
                )

            session.commit()

            return (
                True,
                (
                    f"Deleted {len(movements)} "
                    "car movement(s)."
                ),
            )