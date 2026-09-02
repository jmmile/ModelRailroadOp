from sqlalchemy import (
    select,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.operations_session_train import (
    OperationsSessionTrain,
)


class OperationsSessionTrainService:
    """
    Service for managing the relationship between
    Operations Sessions and Trains.
    """

    #
    # Get all Operations Session / Train assignments.
    #

    @staticmethod
    def get_all():

        with SessionLocal() as session:

            statement = (
                select(
                    OperationsSessionTrain
                )
                .order_by(
                    OperationsSessionTrain.operations_session_id,
                    OperationsSessionTrain.id,
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
    # Get assignment by ID.
    #

    @staticmethod
    def get_by_id(
        assignment_id,
    ):

        if assignment_id is None:

            return None

        with SessionLocal() as session:

            return session.get(
                OperationsSessionTrain,
                assignment_id,
            )

    #
    # Get assignments for an Operations Session.
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
                    OperationsSessionTrain
                )
                .where(
                    OperationsSessionTrain.operations_session_id
                    == operations_session_id
                )
                .order_by(
                    OperationsSessionTrain.id,
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
    # Get assignments for a Train.
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
                    OperationsSessionTrain
                )
                .where(
                    OperationsSessionTrain.train_id
                    == train_id
                )
                .order_by(
                    OperationsSessionTrain.operations_session_id,
                    OperationsSessionTrain.id,
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
    # Create assignment.
    #

    @staticmethod
    def create(
        operations_session_id,
        train_id,
    ):

        if operations_session_id is None:

            return (
                False,
                "No Operations Session was specified.",
            )

        if train_id is None:

            return (
                False,
                "No train was specified.",
            )

        with SessionLocal() as session:

            #
            # Make sure the same train is not already
            # assigned to this Operations Session.
            #

            existing_statement = (
                select(
                    OperationsSessionTrain
                )
                .where(
                    OperationsSessionTrain.operations_session_id
                    == operations_session_id
                )
                .where(
                    OperationsSessionTrain.train_id
                    == train_id
                )
            )

            existing = (
                session.execute(
                    existing_statement
                )
                .scalars()
                .first()
            )

            if existing is not None:

                return (
                    False,
                    "That train is already assigned "
                    "to this Operations Session.",
                )

            #
            # Create assignment.
            #

            assignment = OperationsSessionTrain(
                operations_session_id=(
                    operations_session_id
                ),
                train_id=train_id,
            )

            session.add(
                assignment
            )

            session.commit()

            session.refresh(
                assignment
            )

            return (
                True,
                assignment,
            )

    #
    # Delete assignment.
    #

    @staticmethod
    def delete(
        assignment_id,
    ):

        if assignment_id is None:

            return (
                False,
                "No train assignment was specified.",
            )

        with SessionLocal() as session:

            assignment = session.get(
                OperationsSessionTrain,
                assignment_id,
            )

            if assignment is None:

                return (
                    False,
                    (
                        f"Train assignment "
                        f"{assignment_id} "
                        "was not found."
                    ),
                )

            session.delete(
                assignment
            )

            session.commit()

            return (
                True,
                "Train assignment deleted successfully.",
            )

    #
    # Delete all assignments for an
    # Operations Session.
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
                    OperationsSessionTrain
                )
                .where(
                    OperationsSessionTrain.operations_session_id
                    == operations_session_id
                )
            )

            assignments = (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

            for assignment in assignments:

                session.delete(
                    assignment
                )

            session.commit()

            return (
                True,
                (
                    f"Deleted {len(assignments)} "
                    "train assignment(s)."
                ),
            )

    #
    # Delete all assignments for a Train.
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

            statement = (
                select(
                    OperationsSessionTrain
                )
                .where(
                    OperationsSessionTrain.train_id
                    == train_id
                )
            )

            assignments = (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

            for assignment in assignments:

                session.delete(
                    assignment
                )

            session.commit()

            return (
                True,
                (
                    f"Deleted {len(assignments)} "
                    "train assignment(s)."
                ),
            )