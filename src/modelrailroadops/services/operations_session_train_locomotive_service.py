from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import (
    joinedload,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.locomotive import (
    Locomotive,
)

from modelrailroadops.models.operations_session_train import (
    OperationsSessionTrain,
)

from modelrailroadops.models.operations_session_train_locomotive import (
    OperationsSessionTrainLocomotive,
)


class OperationsSessionTrainLocomotiveService:
    """
    Service for managing locomotive assignments
    to trains within Operations Sessions.
    """

    @staticmethod
    def get_by_id(
        assignment_id,
    ):

        if assignment_id is None:

            return None

        with SessionLocal() as session:

            statement = (
                select(
                    OperationsSessionTrainLocomotive
                )
                .options(
                    joinedload(
                        OperationsSessionTrainLocomotive.locomotive
                    )
                )
                .where(
                    OperationsSessionTrainLocomotive.id
                    == assignment_id
                )
            )

            return (
                session.execute(
                    statement
                )
                .scalars()
                .first()
            )

    @staticmethod
    def get_by_operations_session_train(
        operations_session_train_id,
    ):

        if operations_session_train_id is None:

            return []

        with SessionLocal() as session:

            statement = (
                select(
                    OperationsSessionTrainLocomotive
                )
                .options(
                    joinedload(
                        OperationsSessionTrainLocomotive.locomotive
                    )
                )
                .where(
                    OperationsSessionTrainLocomotive
                    .operations_session_train_id
                    == operations_session_train_id
                )
                .order_by(
                    OperationsSessionTrainLocomotive.sequence,
                    OperationsSessionTrainLocomotive.id,
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
    def create(
        operations_session_train_id,
        locomotive_id,
    ):

        if operations_session_train_id is None:

            return (
                False,
                "No train assignment was specified.",
            )

        if locomotive_id is None:

            return (
                False,
                "No locomotive was specified.",
            )

        with SessionLocal() as session:

            operations_session_train = session.get(
                OperationsSessionTrain,
                operations_session_train_id,
            )

            if operations_session_train is None:

                return (
                    False,
                    (
                        f"Train assignment "
                        f"{operations_session_train_id} "
                        "was not found."
                    ),
                )

            locomotive = session.get(
                Locomotive,
                locomotive_id,
            )

            if locomotive is None:

                return (
                    False,
                    (
                        f"Locomotive "
                        f"{locomotive_id} "
                        "was not found."
                    ),
                )

            existing_statement = (
                select(
                    OperationsSessionTrainLocomotive
                )
                .where(
                    OperationsSessionTrainLocomotive
                    .operations_session_train_id
                    == operations_session_train_id
                )
                .where(
                    OperationsSessionTrainLocomotive.locomotive_id
                    == locomotive_id
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
                    (
                        f"{locomotive.reporting_mark} "
                        f"{locomotive.number} "
                        "is already assigned to this train."
                    ),
                )

            #
            # Check motive type compatibility.
            #
            # The first locomotive establishes the
            # motive type for the consist.
            #
            # Additional locomotives must normally
            # use the same motive type.
            #

            consist_statement = (
                select(
                    OperationsSessionTrainLocomotive
                )
                .options(
                    joinedload(
                        OperationsSessionTrainLocomotive.locomotive
                    )
                )
                .where(
                    OperationsSessionTrainLocomotive
                    .operations_session_train_id
                    == operations_session_train_id
                )
                .order_by(
                    OperationsSessionTrainLocomotive.sequence,
                    OperationsSessionTrainLocomotive.id,
                )
            )

            consist = (
                session.execute(
                    consist_statement
                )
                .scalars()
                .all()
            )

            if consist:

                lead_assignment = consist[0]

                lead_locomotive = (
                    lead_assignment.locomotive
                )

                lead_type = (
                    lead_locomotive.locomotive_type
                    or ""
                ).strip().lower()

                new_type = (
                    locomotive.locomotive_type
                    or ""
                ).strip().lower()

                if lead_type != new_type:

                    return (
                        False,
                        (
                            f"{locomotive.reporting_mark} "
                            f"{locomotive.number} "
                            f"is a "
                            f"{locomotive.locomotive_type} "
                            "locomotive and cannot normally "
                            "be combined with the existing "
                            f"{lead_locomotive.locomotive_type} "
                            "locomotive consist."
                        ),
                    )

            sequence_statement = (
                select(
                    func.max(
                        OperationsSessionTrainLocomotive.sequence
                    )
                )
                .where(
                    OperationsSessionTrainLocomotive
                    .operations_session_train_id
                    == operations_session_train_id
                )
            )

            current_maximum = session.execute(
                sequence_statement
            ).scalar_one_or_none()

            next_sequence = (
                current_maximum + 1
                if current_maximum is not None
                else 1
            )

            assignment = OperationsSessionTrainLocomotive(
                operations_session_train_id=(
                    operations_session_train_id
                ),
                locomotive_id=locomotive_id,
                sequence=next_sequence,
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

    @staticmethod
    def delete(
        assignment_id,
    ):

        if assignment_id is None:

            return (
                False,
                "No locomotive assignment was specified.",
            )

        with SessionLocal() as session:

            assignment = session.get(
                OperationsSessionTrainLocomotive,
                assignment_id,
            )

            if assignment is None:

                return (
                    False,
                    (
                        f"Locomotive assignment "
                        f"{assignment_id} "
                        "was not found."
                    ),
                )

            operations_session_train_id = (
                assignment.operations_session_train_id
            )

            session.delete(
                assignment
            )

            session.flush()

            remaining_statement = (
                select(
                    OperationsSessionTrainLocomotive
                )
                .where(
                    OperationsSessionTrainLocomotive
                    .operations_session_train_id
                    == operations_session_train_id
                )
                .order_by(
                    OperationsSessionTrainLocomotive.sequence,
                    OperationsSessionTrainLocomotive.id,
                )
            )

            remaining_assignments = (
                session.execute(
                    remaining_statement
                )
                .scalars()
                .all()
            )

            for sequence, remaining_assignment in enumerate(
                remaining_assignments,
                start=1,
            ):

                remaining_assignment.sequence = sequence

            session.commit()

            return (
                True,
                "Locomotive assignment deleted successfully.",
            )

    @staticmethod
    def delete_by_operations_session_train(
        operations_session_train_id,
    ):

        if operations_session_train_id is None:

            return (
                False,
                "No train assignment was specified.",
            )

        with SessionLocal() as session:

            statement = (
                select(
                    OperationsSessionTrainLocomotive
                )
                .where(
                    OperationsSessionTrainLocomotive
                    .operations_session_train_id
                    == operations_session_train_id
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
                    "locomotive assignment(s)."
                ),
            )