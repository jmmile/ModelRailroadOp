from datetime import date

import pytest
from sqlalchemy import func, select

from modelrailroadops.models.car import Car
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.car_movement import CarMovement
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.train import Train
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.car_location_service import (
    CarLocationService,
)
from modelrailroadops.services.operations_session_service import (
    OperationsSessionService,
)
from modelrailroadops.services.switch_list_move_service import (
    SwitchListMoveService,
)


def seed_general_track_waybill(
    test_database,
    session_status="PLANNED",
):
    """
    Create a car moving from staging to a general yard track.

    The Waybill receives one PICKUP and one SETOUT CarMove
    assigned to the same Train so the operating lifecycle can
    be tested one instruction at a time.
    """

    with test_database.SessionLocal() as session:

        staging = Location(
            name="Staging Yard",
            location_type="STAGING",
            active=True,
        )

        weston = Location(
            name="Weston",
            location_type="YARD",
            active=True,
        )

        session.add_all(
            (
                staging,
                weston,
            )
        )

        session.flush()

        staging_track = LocationTrack(
            location_id=staging.id,
            name="Eastbound",
            track_type="STAGING",
            traffic_use="BOTH",
            capacity=10,
            active=True,
        )

        weston_track = LocationTrack(
            location_id=weston.id,
            name="Arrival",
            track_type="YARD",
            traffic_use="ARRIVAL",
            capacity=10,
            active=True,
        )

        session.add_all(
            (
                staging_track,
                weston_track,
            )
        )

        session.flush()

        car = Car(
            reporting_mark="TEST",
            number="1001",
            owner="Test Railroad",
            car_type="Boxcar",
            length=50,
            status="AVAILABLE",
            location="Staging Yard - Eastbound",
            operating_location_id=staging.id,
            operating_track_id=staging_track.id,
        )

        operations_session = OperationsSession(
            name="Weston Turn",
            session_date=date(
                2026,
                9,
                1,
            ),
            status=session_status,
        )

        train = Train(
            number="101",
            name="Weston Turn",
            train_type="FREIGHT",
            active=True,
        )

        session.add_all(
            (
                car,
                operations_session,
                train,
            )
        )

        session.flush()

        waybill = Waybill(
            car_id=car.id,
            operations_session_id=operations_session.id,
            origin_location="Staging Yard",
            origin_location_id=staging.id,
            origin_location_track_id=staging_track.id,
            destination_location_id=weston.id,
            destination_location_track_id=weston_track.id,
            load_state="EMPTY",
            cargo_weight_lbs=0,
            status="ACTIVE",
        )

        session.add(
            waybill
        )

        session.flush()

        pickup = CarMove(
            operations_session_id=operations_session.id,
            train_id=train.id,
            car_id=car.id,
            waybill_id=waybill.id,
            route_sequence=1,
            move_type="PICKUP",
            status="PENDING",
            origin_location="Staging Yard",
            destination_location="Weston",
            notes="Pickup test car",
        )

        setout = CarMove(
            operations_session_id=operations_session.id,
            train_id=train.id,
            car_id=car.id,
            waybill_id=waybill.id,
            route_sequence=2,
            move_type="SETOUT",
            status="PENDING",
            origin_location="Staging Yard",
            destination_location="Weston",
            notes="Setout test car",
        )

        session.add_all(
            (
                pickup,
                setout,
            )
        )

        session.commit()

        return {
            "car_id": car.id,
            "train_id": train.id,
            "operations_session_id": operations_session.id,
            "waybill_id": waybill.id,
            "pickup_id": pickup.id,
            "setout_id": setout.id,
            "source_location_id": staging.id,
            "source_track_id": staging_track.id,
            "destination_location_id": weston.id,
            "destination_track_id": weston_track.id,
        }


def test_direct_car_move_does_not_start_planned_session(
    test_database,
):
    """
    A physical car-location move must not implicitly start a
    PLANNED Operations Session.

    The Operations/Switch List workflow starts the session when
    the first PICKUP instruction is completed.
    """

    record_ids = seed_general_track_waybill(
        test_database
    )

    moved, message = (
        CarLocationService.move_car_to_location_track_with_message(
            record_ids["car_id"],
            record_ids["destination_track_id"],
            operations_session_id=(
                record_ids["operations_session_id"]
            ),
        )
    )

    assert not moved
    assert "planned" in message.casefold()

    with test_database.SessionLocal() as session:

        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )

        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        pickup = session.get(
            CarMove,
            record_ids["pickup_id"],
        )

        setout = session.get(
            CarMove,
            record_ids["setout_id"],
        )

        car = session.get(
            Car,
            record_ids["car_id"],
        )

        movement_count = session.scalar(
            select(func.count())
            .select_from(CarMovement)
        )

        assert operations_session.status == "PLANNED"

        assert waybill.status == "ACTIVE"
        assert waybill.completed_at is None

        assert pickup.status == "PENDING"
        assert pickup.completed_at is None

        assert setout.status == "PENDING"
        assert setout.completed_at is None

        assert (
            car.operating_location_id
            == record_ids["source_location_id"]
        )

        assert (
            car.operating_track_id
            == record_ids["source_track_id"]
        )

        assert car.location == "Staging Yard - Eastbound"

        assert movement_count == 0


def test_pickup_starts_planned_session_and_marks_waybill_in_progress(
    test_database,
):
    record_ids = seed_general_track_waybill(
        test_database
    )

    can_complete, message = (
        SwitchListMoveService.can_complete_move(
            record_ids["pickup_id"]
        )
    )

    assert can_complete, message

    with test_database.SessionLocal() as session:

        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )

        assert operations_session.status == "PLANNED"

    completed, message = (
        SwitchListMoveService.complete_move(
            record_ids["pickup_id"]
        )
    )

    assert completed, message

    with test_database.SessionLocal() as session:

        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )

        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        pickup = session.get(
            CarMove,
            record_ids["pickup_id"],
        )

        setout = session.get(
            CarMove,
            record_ids["setout_id"],
        )

        car = session.get(
            Car,
            record_ids["car_id"],
        )

        movement_count = session.scalar(
            select(func.count())
            .select_from(CarMovement)
        )

        assert operations_session.status == "ACTIVE"

        assert waybill.status == "IN_PROGRESS"
        assert waybill.completed_at is None

        assert pickup.status == "COMPLETED"
        assert pickup.completed_at is not None

        assert setout.status == "PENDING"
        assert setout.completed_at is None

        assert (
            car.operating_location_id
            == record_ids["source_location_id"]
        )

        assert (
            car.operating_track_id
            == record_ids["source_track_id"]
        )

        assert car.location == "Staging Yard - Eastbound"

        assert movement_count == 0


def test_setout_cannot_complete_before_pickup(
    test_database,
):
    record_ids = seed_general_track_waybill(
        test_database
    )

    can_complete, message = (
        SwitchListMoveService.can_complete_move(
            record_ids["setout_id"]
        )
    )

    assert not can_complete
    assert "pickup" in message.casefold()

    completed, message = (
        SwitchListMoveService.complete_move(
            record_ids["setout_id"]
        )
    )

    assert not completed
    assert "pickup" in message.casefold()

    with test_database.SessionLocal() as session:

        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )

        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        setout = session.get(
            CarMove,
            record_ids["setout_id"],
        )

        car = session.get(
            Car,
            record_ids["car_id"],
        )

        movement_count = session.scalar(
            select(func.count())
            .select_from(CarMovement)
        )

        assert operations_session.status == "PLANNED"
        assert waybill.status == "ACTIVE"

        assert setout.status == "PENDING"
        assert setout.completed_at is None

        assert (
            car.operating_track_id
            == record_ids["source_track_id"]
        )

        assert movement_count == 0


def test_pickup_then_setout_completes_waybill_and_moves_car(
    test_database,
):
    record_ids = seed_general_track_waybill(
        test_database
    )

    completed, message = (
        SwitchListMoveService.complete_move(
            record_ids["pickup_id"]
        )
    )

    assert completed, message

    completed, message = (
        SwitchListMoveService.complete_move(
            record_ids["setout_id"]
        )
    )

    assert completed, message

    with test_database.SessionLocal() as session:

        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )

        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        pickup = session.get(
            CarMove,
            record_ids["pickup_id"],
        )

        setout = session.get(
            CarMove,
            record_ids["setout_id"],
        )

        car = session.get(
            Car,
            record_ids["car_id"],
        )

        movements = (
            session.execute(
                select(
                    CarMovement
                )
            )
            .scalars()
            .all()
        )

        assert operations_session.status == "ACTIVE"

        assert waybill.status == "COMPLETED"
        assert waybill.completed_at is not None

        assert pickup.status == "COMPLETED"
        assert pickup.completed_at is not None

        assert setout.status == "COMPLETED"
        assert setout.completed_at is not None

        assert (
            car.operating_location_id
            == record_ids["destination_location_id"]
        )

        assert (
            car.operating_track_id
            == record_ids["destination_track_id"]
        )

        assert car.industry_id is None
        assert car.track_id is None
        assert car.spot_id is None

        assert car.location == "Weston - Arrival"

        assert len(movements) == 1

        assert (
            movements[0].operations_session_id
            == operations_session.id
        )

        assert (
            movements[0].from_location
            == "Staging Yard - Eastbound"
        )

        assert (
            movements[0].to_location
            == "Weston - Arrival"
        )


def test_session_can_be_completed_after_setout(
    test_database,
):
    record_ids = seed_general_track_waybill(
        test_database
    )

    completed, message = (
        SwitchListMoveService.complete_move(
            record_ids["pickup_id"]
        )
    )

    assert completed, message

    completed, message = (
        SwitchListMoveService.complete_move(
            record_ids["setout_id"]
        )
    )

    assert completed, message

    completed, result = (
        OperationsSessionService.complete(
            record_ids["operations_session_id"]
        )
    )

    assert completed, result

    with test_database.SessionLocal() as session:

        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )

        assert operations_session.status == "COMPLETED"
        assert operations_session.completed_at is not None


def test_failed_setout_does_not_move_car_or_complete_waybill(
    test_database,
):
    record_ids = seed_general_track_waybill(
        test_database
    )

    completed, message = (
        SwitchListMoveService.complete_move(
            record_ids["pickup_id"]
        )
    )

    assert completed, message

    with test_database.SessionLocal() as session:

        destination_track = session.get(
            LocationTrack,
            record_ids["destination_track_id"],
        )

        destination_track.capacity = 0

        session.commit()

    completed, message = (
        SwitchListMoveService.complete_move(
            record_ids["setout_id"]
        )
    )

    assert not completed
    assert "capacity" in message.casefold()

    with test_database.SessionLocal() as session:

        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )

        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        pickup = session.get(
            CarMove,
            record_ids["pickup_id"],
        )

        setout = session.get(
            CarMove,
            record_ids["setout_id"],
        )

        car = session.get(
            Car,
            record_ids["car_id"],
        )

        movement_count = session.scalar(
            select(func.count())
            .select_from(CarMovement)
        )

        assert operations_session.status == "ACTIVE"

        assert waybill.status == "IN_PROGRESS"
        assert waybill.completed_at is None

        assert pickup.status == "COMPLETED"

        assert setout.status == "PENDING"
        assert setout.completed_at is None

        assert (
            car.operating_location_id
            == record_ids["source_location_id"]
        )

        assert (
            car.operating_track_id
            == record_ids["source_track_id"]
        )

        assert car.location == "Staging Yard - Eastbound"

        assert movement_count == 0


@pytest.mark.parametrize(
    "session_status",
    [
        "COMPLETED",
        "CANCELLED",
    ],
)
def test_terminal_session_rejects_car_moves(
    test_database,
    session_status,
):
    record_ids = seed_general_track_waybill(
        test_database,
        session_status,
    )

    completed, message = (
        SwitchListMoveService.complete_move(
            record_ids["pickup_id"]
        )
    )

    assert not completed
    assert session_status in message

    with test_database.SessionLocal() as session:

        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        pickup = session.get(
            CarMove,
            record_ids["pickup_id"],
        )

        setout = session.get(
            CarMove,
            record_ids["setout_id"],
        )

        car = session.get(
            Car,
            record_ids["car_id"],
        )

        movement_count = session.scalar(
            select(func.count())
            .select_from(CarMovement)
        )

        assert waybill.status == "ACTIVE"

        assert pickup.status == "PENDING"
        assert setout.status == "PENDING"

        assert (
            car.operating_track_id
            == record_ids["source_track_id"]
        )

        assert movement_count == 0