from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import (
    joinedload,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.operations_session_train import (
    OperationsSessionTrain,
)

from modelrailroadops.models.operations_session_train_passenger_car import (
    OperationsSessionTrainPassengerCar,
)

from modelrailroadops.models.passenger_car import (
    PassengerCar,
)


class OperationsSessionTrainPassengerCarService:
    """
    Service for managing passenger car assignments
    to passenger trains within Operations Sessions.
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
                    OperationsSessionTrainPassengerCar
                )
                .options(
                    joinedload(
                        OperationsSessionTrainPassengerCar.passenger_car
                    )
                )
                .where(
                    OperationsSessionTrainPassengerCar.id
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
                    OperationsSessionTrainPassengerCar
                )
                .options(
                    joinedload(
                        OperationsSessionTrainPassengerCar.passenger_car
                    )
                )
                .where(
                    OperationsSessionTrainPassengerCar
                    .operations_session_train_id
                    == operations_session_train_id
                )
                .order_by(
                    OperationsSessionTrainPassengerCar.sequence,
                    OperationsSessionTrainPassengerCar.id,
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
        passenger_car_id,
    ):

        if operations_session_train_id is None:

            return (
                False,
                "No train assignment was specified.",
            )

        if passenger_car_id is None:

            return (
                False,
                "No passenger car was specified.",
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

            train = (
                operations_session_train.train
            )

            train_type = (
                train.train_type
                or ""
            ).strip().upper()

            if train_type != "PASSENGER":

                return (
                    False,
                    (
                        f"Train {train.number} "
                        "is not a passenger train. "
                        "Passenger equipment can only be "
                        "assigned to passenger trains."
                    ),
                )

            passenger_car = session.get(
                PassengerCar,
                passenger_car_id,
            )

            if passenger_car is None:

                return (
                    False,
                    (
                        f"Passenger car "
                        f"{passenger_car_id} "
                        "was not found."
                    ),
                )

            passenger_car_status = (
                passenger_car.status
                or ""
            ).strip().upper()

            if passenger_car_status == "OUT_OF_SERVICE":

                return (
                    False,
                    (
                        f"{passenger_car.reporting_mark} "
                        f"{passenger_car.number} "
                        "is out of service and cannot "
                        "be assigned to a train."
                    ),
                )

            existing_statement = (
                select(
                    OperationsSessionTrainPassengerCar
                )
                .where(
                    OperationsSessionTrainPassengerCar
                    .operations_session_train_id
                    == operations_session_train_id
                )
                .where(
                    OperationsSessionTrainPassengerCar
                    .passenger_car_id
                    == passenger_car_id
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
                        f"{passenger_car.reporting_mark} "
                        f"{passenger_car.number} "
                        "is already assigned to this train."
                    ),
                )

            session_existing_statement = (
                select(
                    OperationsSessionTrainPassengerCar
                )
                .join(
                    OperationsSessionTrain,
                    (
                        OperationsSessionTrain.id
                        == OperationsSessionTrainPassengerCar
                        .operations_session_train_id
                    ),
                )
                .where(
                    OperationsSessionTrain.operations_session_id
                    == operations_session_train.operations_session_id
                )
                .where(
                    OperationsSessionTrainPassengerCar
                    .passenger_car_id
                    == passenger_car_id
                )
            )

            session_existing = (
                session.execute(
                    session_existing_statement
                )
                .scalars()
                .first()
            )

            if session_existing is not None:

                other_train_assignment = session.get(
                    OperationsSessionTrain,
                    session_existing.operations_session_train_id,
                )

                other_train = (
                    other_train_assignment.train
                    if other_train_assignment is not None
                    else None
                )

                other_train_description = (
                    (
                        f"{other_train.symbol or ''} - "
                        f"{other_train.name or ''}"
                    ).strip(" -")
                    if other_train is not None
                    else "another train"
                )

                return (
                    False,
                    (
                        f"{passenger_car.reporting_mark} "
                        f"{passenger_car.number} "
                        "is already assigned to "
                        f"{other_train_description} "
                        "in this Operations Session."
                    ),
                )

            sequence_statement = (
                select(
                    func.max(
                        OperationsSessionTrainPassengerCar.sequence
                    )
                )
                .where(
                    OperationsSessionTrainPassengerCar
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

            assignment = OperationsSessionTrainPassengerCar(
                operations_session_train_id=(
                    operations_session_train_id
                ),
                passenger_car_id=passenger_car_id,
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
    def move_up(
        assignment_id,
    ):

        if assignment_id is None:

            return (
                False,
                "No passenger car assignment was specified.",
            )

        with SessionLocal() as session:

            assignment = session.get(
                OperationsSessionTrainPassengerCar,
                assignment_id,
            )

            if assignment is None:

                return (
                    False,
                    (
                        f"Passenger car assignment "
                        f"{assignment_id} "
                        "was not found."
                    ),
                )

            previous_statement = (
                select(
                    OperationsSessionTrainPassengerCar
                )
                .where(
                    OperationsSessionTrainPassengerCar
                    .operations_session_train_id
                    == assignment.operations_session_train_id
                )
                .where(
                    OperationsSessionTrainPassengerCar.sequence
                    < assignment.sequence
                )
                .order_by(
                    OperationsSessionTrainPassengerCar.sequence.desc(),
                    OperationsSessionTrainPassengerCar.id.desc(),
                )
            )

            previous_assignment = (
                session.execute(
                    previous_statement
                )
                .scalars()
                .first()
            )

            if previous_assignment is None:

                return (
                    False,
                    (
                        "The passenger car is already "
                        "first in the consist."
                    ),
                )

            current_sequence = assignment.sequence

            previous_sequence = (
                previous_assignment.sequence
            )

            temporary_sequence = (
                -assignment.id
            )

            assignment.sequence = temporary_sequence

            session.flush()

            previous_assignment.sequence = (
                current_sequence
            )

            session.flush()

            assignment.sequence = (
                previous_sequence
            )

            session.commit()

            return (
                True,
                "Passenger car moved up successfully.",
            )

    @staticmethod
    def move_down(
        assignment_id,
    ):

        if assignment_id is None:

            return (
                False,
                "No passenger car assignment was specified.",
            )

        with SessionLocal() as session:

            assignment = session.get(
                OperationsSessionTrainPassengerCar,
                assignment_id,
            )

            if assignment is None:

                return (
                    False,
                    (
                        f"Passenger car assignment "
                        f"{assignment_id} "
                        "was not found."
                    ),
                )

            next_statement = (
                select(
                    OperationsSessionTrainPassengerCar
                )
                .where(
                    OperationsSessionTrainPassengerCar
                    .operations_session_train_id
                    == assignment.operations_session_train_id
                )
                .where(
                    OperationsSessionTrainPassengerCar.sequence
                    > assignment.sequence
                )
                .order_by(
                    OperationsSessionTrainPassengerCar.sequence,
                    OperationsSessionTrainPassengerCar.id,
                )
            )

            next_assignment = (
                session.execute(
                    next_statement
                )
                .scalars()
                .first()
            )

            if next_assignment is None:

                return (
                    False,
                    (
                        "The passenger car is already "
                        "last in the consist."
                    ),
                )

            current_sequence = assignment.sequence

            next_sequence = (
                next_assignment.sequence
            )

            temporary_sequence = (
                -assignment.id
            )

            assignment.sequence = temporary_sequence

            session.flush()

            next_assignment.sequence = (
                current_sequence
            )

            session.flush()

            assignment.sequence = (
                next_sequence
            )

            session.commit()

            return (
                True,
                "Passenger car moved down successfully.",
            )

    @staticmethod
    def delete(
        assignment_id,
    ):

        if assignment_id is None:

            return (
                False,
                "No passenger car assignment was specified.",
            )

        with SessionLocal() as session:

            assignment = session.get(
                OperationsSessionTrainPassengerCar,
                assignment_id,
            )

            if assignment is None:

                return (
                    False,
                    (
                        f"Passenger car assignment "
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
                    OperationsSessionTrainPassengerCar
                )
                .where(
                    OperationsSessionTrainPassengerCar
                    .operations_session_train_id
                    == operations_session_train_id
                )
                .order_by(
                    OperationsSessionTrainPassengerCar.sequence,
                    OperationsSessionTrainPassengerCar.id,
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
                "Passenger car assignment deleted successfully.",
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
                    OperationsSessionTrainPassengerCar
                )
                .where(
                    OperationsSessionTrainPassengerCar
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
                    "passenger car assignment(s)."
                ),
            )