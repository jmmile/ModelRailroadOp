from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.waybill_service import WaybillService


class OperationsSessionService:
    """Create, retrieve, and manage Operations Sessions."""

    @staticmethod
    def get_all():
        with SessionLocal() as session:
            return session.execute(
                select(OperationsSession).order_by(
                    OperationsSession.session_date.desc(),
                    OperationsSession.id.desc(),
                )
            ).scalars().all()

    @staticmethod
    def get_by_id(session_id):
        if session_id is None:
            return None

        with SessionLocal() as session:
            return session.get(
                OperationsSession,
                session_id,
            )

    @staticmethod
    def create(
        name,
        session_date,
        notes=None,
    ):
        name = name.strip() if name else ""

        if not name:
            return False, "Operations Session name is required."

        if session_date is None:
            return False, "Operations Session date is required."

        notes = notes.strip() if notes else None

        with SessionLocal() as session:
            operations_session = OperationsSession(
                name=name,
                session_date=session_date,
                notes=notes,
                status="PLANNED",
            )

            session.add(
                operations_session
            )

            session.commit()

            session.refresh(
                operations_session
            )

            return True, operations_session

    @staticmethod
    def update(
        session_id,
        name,
        session_date,
        notes=None,
    ):
        if session_id is None:
            return (
                False,
                "No Operations Session was specified.",
            )

        name = name.strip() if name else ""

        if not name:
            return (
                False,
                "Operations Session name is required.",
            )

        if session_date is None:
            return (
                False,
                "Operations Session date is required.",
            )

        notes = notes.strip() if notes else None

        with SessionLocal() as session:
            operations_session = session.get(
                OperationsSession,
                session_id,
            )

            if operations_session is None:
                return (
                    False,
                    (
                        f"Operations Session "
                        f"{session_id} was not found."
                    ),
                )

            operations_session.name = name
            operations_session.session_date = session_date
            operations_session.notes = notes

            session.commit()

            session.refresh(
                operations_session
            )

            return True, operations_session

    @staticmethod
    def start(
        session_id,
    ):
        if session_id is None:
            return (
                False,
                "No Operations Session was specified.",
            )

        with SessionLocal() as session:
            operations_session = session.get(
                OperationsSession,
                session_id,
            )

            if operations_session is None:
                return (
                    False,
                    (
                        f"Operations Session "
                        f"{session_id} was not found."
                    ),
                )

            if operations_session.status != "PLANNED":
                return (
                    False,
                    (
                        "Only a PLANNED Operations Session "
                        "can be started."
                    ),
                )

            operations_session.status = "ACTIVE"

            session.commit()

            session.refresh(
                operations_session
            )

            return True, operations_session

    @staticmethod
    def _validate_completion_readiness(
        session,
        session_id,
    ):
        """
        Validate whether an Operations Session is ready
        to be completed.

        This method does not change database state.

        Returns:

            (True, unfinished_waybills)

        when every unfinished Waybill can be completed.

        Otherwise returns:

            (False, message)
        """

        operations_session = session.get(
            OperationsSession,
            session_id,
        )

        if operations_session is None:
            return (
                False,
                (
                    f"Operations Session "
                    f"{session_id} was not found."
                ),
            )

        if operations_session.status != "ACTIVE":
            return (
                False,
                (
                    "Only an ACTIVE Operations Session "
                    "can be completed."
                ),
            )

        unfinished_waybills = (
            session.execute(
                select(
                    Waybill
                )
                .where(
                    Waybill.operations_session_id
                    == session_id,
                    Waybill.status.in_(
                        [
                            "ACTIVE",
                            "IN_PROGRESS",
                        ]
                    ),
                )
                .order_by(
                    Waybill.id
                )
            )
            .scalars()
            .all()
        )

        incomplete = []

        for waybill in unfinished_waybills:
            valid, message = (
                WaybillService.validate_completion(
                    waybill.id,
                    db_session=session,
                )
            )

            if not valid:
                incomplete.append(
                    (
                        f"Waybill "
                        f"#{waybill.id}: "
                        f"{message}"
                    )
                )

        if incomplete:
            return (
                False,
                (
                    "The Operations Session cannot be "
                    "completed because these Waybills "
                    "are unfinished:\n\n"
                    + "\n".join(
                        incomplete
                    )
                ),
            )

        return (
            True,
            unfinished_waybills,
        )

    @staticmethod
    def can_complete(
        session_id,
    ):
        """
        Check whether an Operations Session is ready
        to be completed without changing database state.
        """

        if session_id is None:
            return (
                False,
                "No Operations Session was specified.",
            )

        with SessionLocal() as session:
            ready, result = (
                OperationsSessionService
                ._validate_completion_readiness(
                    session,
                    session_id,
                )
            )

            if not ready:
                return (
                    False,
                    result,
                )

            return (
                True,
                (
                    "Operations Session is ready "
                    "to be completed."
                ),
            )

    @staticmethod
    def complete(
        session_id,
    ):
        """
        Complete a session only when every unfinished
        Waybill arrives.

        The preflight validates all Waybills before any
        status changes.

        The subsequent Waybill and Operations Session
        changes share one transaction, so a failed
        completion never leaves a partially completed
        session.
        """

        if session_id is None:
            return (
                False,
                "No Operations Session was specified.",
            )

        with SessionLocal() as session:
            ready, result = (
                OperationsSessionService
                ._validate_completion_readiness(
                    session,
                    session_id,
                )
            )

            if not ready:
                return (
                    False,
                    result,
                )

            unfinished_waybills = result

            operations_session = session.get(
                OperationsSession,
                session_id,
            )

            for waybill in unfinished_waybills:
                success, result = (
                    WaybillService.complete(
                        waybill.id,
                        db_session=session,
                    )
                )

                if not success:
                    session.rollback()

                    return (
                        False,
                        result,
                    )

            operations_session.status = "COMPLETED"

            operations_session.completed_at = (
                datetime.now(UTC).replace(tzinfo=None)
            )

            session.commit()

            session.refresh(
                operations_session
            )

            return (
                True,
                operations_session,
            )

    @staticmethod
    def cancel(
        session_id,
    ):
        if session_id is None:
            return (
                False,
                "No Operations Session was specified.",
            )

        with SessionLocal() as session:
            operations_session = session.get(
                OperationsSession,
                session_id,
            )

            if operations_session is None:
                return (
                    False,
                    (
                        f"Operations Session "
                        f"{session_id} was not found."
                    ),
                )

            if operations_session.status not in (
                "PLANNED",
                "ACTIVE",
            ):
                return (
                    False,
                    (
                        "Only a PLANNED or ACTIVE "
                        "Operations Session can be "
                        "cancelled."
                    ),
                )

            onboard_cars = (
                session.execute(
                    select(Car).distinct()
                    .join(
                        CarMove,
                        CarMove.car_id == Car.id,
                    )
                    .where(
                        CarMove.operations_session_id == session_id,
                        CarMove.move_type == "SETOUT",
                        CarMove.status == "PENDING",
                        Car.location.like("On Train:%"),
                    )
                    .order_by(
                        Car.reporting_mark,
                        Car.number,
                    )
                )
                .scalars()
                .all()
            )

            if onboard_cars:
                car_names = ", ".join(
                    f"{car.reporting_mark} {car.number}"
                    for car in onboard_cars
                )

                return (
                    False,
                    (
                        "The Operations Session cannot be cancelled while "
                        f"cars remain on trains: {car_names}. Return or "
                        "set out these cars first."
                    ),
                )

            operations_session.status = "CANCELLED"

            session.commit()

            session.refresh(
                operations_session
            )

            return (
                True,
                operations_session,
            )

    @staticmethod
    def delete(
        session_id,
    ):
        if session_id is None:
            return (
                False,
                "No Operations Session was specified.",
            )

        with SessionLocal() as session:
            operations_session = session.get(
                OperationsSession,
                session_id,
            )

            if operations_session is None:
                return (
                    False,
                    (
                        f"Operations Session "
                        f"{session_id} was not found."
                    ),
                )

            if operations_session.status == "COMPLETED":
                return (
                    False,
                    "A completed Operations Session cannot be deleted.",
                )

            onboard_cars = (
                session.execute(
                    select(Car).distinct()
                    .join(
                        CarMove,
                        CarMove.car_id == Car.id,
                    )
                    .where(
                        CarMove.operations_session_id == session_id,
                        CarMove.move_type == "SETOUT",
                        CarMove.status == "PENDING",
                        Car.location.like("On Train:%"),
                    )
                    .order_by(
                        Car.reporting_mark,
                        Car.number,
                    )
                )
                .scalars()
                .all()
            )

            if onboard_cars:
                car_names = ", ".join(
                    f"{car.reporting_mark} {car.number}"
                    for car in onboard_cars
                )

                return (
                    False,
                    (
                        "The Operations Session cannot be deleted while "
                        f"cars remain on trains: {car_names}. Return or "
                        "set out these cars first."
                    ),
                )

            session.delete(
                operations_session
            )

            session.commit()

            return (
                True,
                "Operations Session deleted successfully.",
            )

    @staticmethod
    def get_waybills_by_session(
        session_id,
    ):
        if session_id is None:
            return []

        with SessionLocal() as session:
            return (
                session.execute(
                    select(
                        Waybill
                    )
                    .options(
                        joinedload(
                            Waybill.car
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
                    .where(
                        Waybill.operations_session_id
                        == session_id
                    )
                    .order_by(
                        Waybill.id
                    )
                )
                .scalars()
                .unique()
                .all()
            )

    @staticmethod
    def get_waybills(
        session_id,
    ):
        return (
            OperationsSessionService
            .get_waybills_by_session(
                session_id
            )
        )
