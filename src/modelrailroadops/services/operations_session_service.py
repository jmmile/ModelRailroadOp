from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.operations_session_train import OperationsSessionTrain
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.train_route import TrainRoute
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.car_location_service import CarLocationService
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
    def validate_pre_session(session_id):
        """Return a read-only readiness report for an Operations Session."""
        report = {
            "session_name": "",
            "errors": [],
            "warnings": [],
            "passed": [],
        }
        if session_id is None:
            report["errors"].append("No Operations Session was specified.")
            return False, report

        with SessionLocal() as session:
            operations_session = session.get(OperationsSession, session_id)
            if operations_session is None:
                report["errors"].append(
                    f"Operations Session {session_id} was not found."
                )
                return False, report

            report["session_name"] = operations_session.name
            if operations_session.status != "PLANNED":
                report["warnings"].append(
                    f"Session status is {operations_session.status}, not PLANNED."
                )

            assignments = session.execute(
                select(OperationsSessionTrain).where(
                    OperationsSessionTrain.operations_session_id == session_id
                )
            ).scalars().all()
            assigned_train_ids = {
                assignment.train_id for assignment in assignments
            }
            if not assignments:
                report["errors"].append("No trains are assigned to this session.")
            else:
                report["passed"].append(
                    f"{len(assignments)} train assignment(s) found."
                )

            for assignment in assignments:
                train = assignment.train
                train_name = train.symbol or train.name
                routes = session.execute(
                    select(TrainRoute)
                    .where(TrainRoute.train_id == train.id)
                    .order_by(TrainRoute.sequence)
                ).scalars().all()
                if len(routes) < 2:
                    report["errors"].append(
                        f"Train {train_name} needs at least two route stops."
                    )
                elif len({route.sequence for route in routes}) != len(routes):
                    report["errors"].append(
                        f"Train {train_name} has duplicate route sequence numbers."
                    )
                else:
                    report["passed"].append(
                        f"Train {train_name} has {len(routes)} ordered route stops."
                    )
                if not assignment.locomotives:
                    report["warnings"].append(
                        f"Train {train_name} has no locomotive assigned."
                    )

            waybills = session.execute(
                select(Waybill).where(
                    Waybill.operations_session_id == session_id,
                    Waybill.archived.is_(False),
                )
            ).scalars().all()
            if not waybills:
                report["warnings"].append(
                    "No non-archived waybills are assigned to this session."
                )
            else:
                report["passed"].append(
                    f"{len(waybills)} non-archived waybill(s) found."
                )

            moves = session.execute(
                select(CarMove).where(CarMove.operations_session_id == session_id)
            ).scalars().all()
            moves_by_waybill = {move.waybill_id for move in moves}
            if waybills and not moves:
                report["warnings"].append(
                    "Car moves have not been generated for this session."
                )

            for move in moves:
                if move.train_id not in assigned_train_ids:
                    report["errors"].append(
                        f"Car move #{move.id} uses a train not assigned to the session."
                    )
                if move.route_sequence is None:
                    report["errors"].append(
                        f"Car move #{move.id} has no route stop sequence."
                    )

            for waybill in waybills:
                car = waybill.car
                car_name = (
                    f"{car.reporting_mark} {car.number}"
                    if car is not None
                    else f"car #{waybill.car_id}"
                )
                if car is None:
                    report["errors"].append(
                        f"Waybill #{waybill.id} references a missing car."
                    )
                    continue

                has_industry_location = all((
                    car.industry_id,
                    car.track_id,
                    car.spot_id,
                ))
                has_general_location = all((
                    car.operating_location_id,
                    car.operating_track_id,
                ))
                if not has_industry_location and not has_general_location:
                    report["errors"].append(
                        f"{car_name} has no complete current location."
                    )

                destination_is_industry = any((
                    waybill.destination_industry_id,
                    waybill.destination_track_id,
                    waybill.destination_spot_id,
                ))
                destination_is_general = any((
                    waybill.destination_location_id,
                    waybill.destination_location_track_id,
                ))
                if not destination_is_industry and not destination_is_general:
                    report["errors"].append(
                        f"Waybill #{waybill.id} for {car_name} has no destination."
                    )
                elif destination_is_industry:
                    if not all((
                        waybill.destination_industry_id,
                        waybill.destination_track_id,
                        waybill.destination_spot_id,
                    )):
                        report["errors"].append(
                            f"Waybill #{waybill.id} for {car_name} has an incomplete industry destination."
                        )
                    else:
                        track = session.get(
                            IndustryTrack,
                            waybill.destination_track_id,
                        )
                        spot = session.get(Spot, waybill.destination_spot_id)
                        if (
                            track is None
                            or track.industry_id != waybill.destination_industry_id
                            or spot is None
                            or spot.track_id != waybill.destination_track_id
                        ):
                            report["errors"].append(
                                f"Waybill #{waybill.id} for {car_name} has mismatched destination records."
                            )
                        else:
                            valid, message = (
                                CarLocationService.validate_car_for_spot(
                                    car,
                                    spot,
                                )
                            )
                            if not valid:
                                report["errors"].append(
                                    f"Waybill #{waybill.id} for {car_name}: {message.replace(chr(10), ' ')}"
                                )
                else:
                    if not all((
                        waybill.destination_location_id,
                        waybill.destination_location_track_id,
                    )):
                        report["errors"].append(
                            f"Waybill #{waybill.id} for {car_name} has an incomplete general-track destination."
                        )
                    else:
                        track = session.get(
                            LocationTrack,
                            waybill.destination_location_track_id,
                        )
                        if (
                            track is None
                            or track.location_id != waybill.destination_location_id
                        ):
                            report["errors"].append(
                                f"Waybill #{waybill.id} for {car_name} has a mismatched general-track destination."
                            )

                if moves and waybill.id not in moves_by_waybill:
                    report["warnings"].append(
                        f"Waybill #{waybill.id} for {car_name} has no generated car moves."
                    )

            general_tracks = session.execute(
                select(LocationTrack).where(
                    LocationTrack.active.is_(True),
                    LocationTrack.capacity.is_not(None),
                )
            ).scalars().all()
            for track in general_tracks:
                occupied = session.scalar(
                    select(func.count(Car.id)).where(
                        Car.operating_track_id == track.id,
                        Car.industry_id.is_(None),
                    )
                )
                if occupied > track.capacity:
                    report["errors"].append(
                        f"Track {track.location.name} — {track.name} is over capacity "
                        f"({occupied}/{track.capacity})."
                    )

            if not report["errors"]:
                report["passed"].append("No blocking readiness errors found.")

            return not report["errors"], report

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
