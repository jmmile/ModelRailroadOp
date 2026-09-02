from datetime import date

import pytest
from sqlalchemy import func, select

from modelrailroadops.models.car import Car
from modelrailroadops.models.car_movement import CarMovement
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.operations_session_service import (
    OperationsSessionService,
)
from modelrailroadops.services.switch_list_move_service import (
    SwitchListMoveService,
)


def seed_general_track_waybill(test_database, session_status="PLANNED"):
    """Create a car moving from staging to a general yard track."""

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
        session.add_all((staging, weston))
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
        session.add_all((staging_track, weston_track))
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
            session_date=date(2026, 9, 1),
            status=session_status,
        )
        session.add_all((car, operations_session))
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
        session.add(waybill)
        session.commit()

        return {
            "car_id": car.id,
            "operations_session_id": operations_session.id,
            "waybill_id": waybill.id,
            "source_track_id": staging_track.id,
            "destination_location_id": weston.id,
            "destination_track_id": weston_track.id,
        }


def test_first_move_starts_planned_session_and_completes_waybill(test_database):
    record_ids = seed_general_track_waybill(test_database)

    can_complete, message = SwitchListMoveService.can_complete_move(
        record_ids["waybill_id"]
    )
    assert can_complete, message

    with test_database.SessionLocal() as session:
        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )
        assert operations_session.status == "PLANNED"

    completed, message = SwitchListMoveService.complete_move(record_ids["waybill_id"])
    assert completed, message

    with test_database.SessionLocal() as session:
        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )
        waybill = session.get(Waybill, record_ids["waybill_id"])
        car = session.get(Car, record_ids["car_id"])
        movements = session.execute(select(CarMovement)).scalars().all()

        assert operations_session.status == "ACTIVE"
        assert waybill.status == "COMPLETED"
        assert waybill.completed_at is not None
        assert car.operating_location_id == record_ids["destination_location_id"]
        assert car.operating_track_id == record_ids["destination_track_id"]
        assert car.industry_id is None
        assert car.track_id is None
        assert car.spot_id is None
        assert car.location == "Weston - Arrival"
        assert len(movements) == 1
        assert movements[0].operations_session_id == operations_session.id
        assert movements[0].from_location == "Staging Yard - Eastbound"
        assert movements[0].to_location == "Weston - Arrival"


def test_session_can_be_completed_after_its_waybill_arrives(test_database):
    record_ids = seed_general_track_waybill(test_database)

    moved, message = SwitchListMoveService.complete_move(record_ids["waybill_id"])
    assert moved, message

    completed, result = OperationsSessionService.complete(
        record_ids["operations_session_id"]
    )
    assert completed, result

    with test_database.SessionLocal() as session:
        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )
        assert operations_session.status == "COMPLETED"
        assert operations_session.completed_at is not None


def test_failed_first_move_does_not_start_planned_session(test_database):
    record_ids = seed_general_track_waybill(test_database)

    with test_database.SessionLocal() as session:
        destination_track = session.get(
            LocationTrack,
            record_ids["destination_track_id"],
        )
        destination_track.capacity = 0
        session.commit()

    completed, message = SwitchListMoveService.complete_move(record_ids["waybill_id"])
    assert not completed
    assert "capacity" in message.casefold()

    with test_database.SessionLocal() as session:
        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )
        waybill = session.get(Waybill, record_ids["waybill_id"])
        car = session.get(Car, record_ids["car_id"])
        movement_count = session.scalar(select(func.count()).select_from(CarMovement))

        assert operations_session.status == "PLANNED"
        assert waybill.status == "ACTIVE"
        assert car.operating_track_id == record_ids["source_track_id"]
        assert movement_count == 0


@pytest.mark.parametrize("session_status", ["COMPLETED", "CANCELLED"])
def test_terminal_session_rejects_car_moves(test_database, session_status):
    record_ids = seed_general_track_waybill(test_database, session_status)

    completed, message = SwitchListMoveService.complete_move(record_ids["waybill_id"])
    assert not completed
    assert session_status in message

    with test_database.SessionLocal() as session:
        waybill = session.get(Waybill, record_ids["waybill_id"])
        car = session.get(Car, record_ids["car_id"])
        movement_count = session.scalar(select(func.count()).select_from(CarMovement))

        assert waybill.status == "ACTIVE"
        assert car.operating_track_id == record_ids["source_track_id"]
        assert movement_count == 0
