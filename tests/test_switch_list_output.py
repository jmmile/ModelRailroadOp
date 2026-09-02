from datetime import date

from sqlalchemy import select

from modelrailroadops.models.car import Car
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.train import Train
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.car_move_service import CarMoveService
from modelrailroadops.services.switch_list_service import SwitchListService


def seed_switch_list(test_database):
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
            active=True,
        )
        weston_track = LocationTrack(
            location_id=weston.id,
            name="Arrival",
            track_type="YARD",
            traffic_use="ARRIVAL",
            active=True,
        )
        session.add_all((staging_track, weston_track))
        session.flush()

        train = Train(
            number="225",
            name="Weston Inbound",
            train_type="Through Freight",
            active=True,
        )
        operations_session = OperationsSession(
            name="Switch List Test",
            session_date=date(2026, 9, 2),
            status="PLANNED",
        )
        car = Car(
            reporting_mark="GN",
            number="33103",
            owner="GN",
            car_type="Gondola",
            length=45,
            status="AVAILABLE",
            location="Staging Yard - Eastbound",
            operating_location_id=staging.id,
            operating_track_id=staging_track.id,
        )
        session.add_all((train, operations_session, car))
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
            notes="Deliver to arrival track",
        )
        session.add(waybill)
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
        )
        setout = CarMove(
            operations_session_id=operations_session.id,
            train_id=train.id,
            car_id=car.id,
            waybill_id=waybill.id,
            route_sequence=3,
            move_type="SETOUT",
            status="PENDING",
            origin_location="Staging Yard",
            destination_location="Weston",
        )
        session.add_all((pickup, setout))
        session.commit()

        return {
            "operations_session_id": operations_session.id,
            "waybill_id": waybill.id,
            "pickup_id": pickup.id,
            "setout_id": setout.id,
        }


def test_switch_list_row_contains_train_route_and_car_details(test_database):
    record_ids = seed_switch_list(test_database)

    rows = SwitchListService.get_switch_list_rows(record_ids["operations_session_id"])

    assert len(rows) == 1
    row = rows[0]
    assert row["train"] == "M225 - Weston Inbound"
    assert row["pickup_sequence"] == 1
    assert row["setout_sequence"] == 3
    assert row["car"] == "GN 33103"
    assert row["car_type"] == "Gondola"
    assert row["length"] == 45
    assert row["origin"] == "Staging Yard - Eastbound"
    assert row["destination"] == "Weston - Arrival"
    assert row["notes"] == "Deliver to arrival track"


def test_completed_waybill_is_removed_from_switch_list(test_database):
    record_ids = seed_switch_list(test_database)

    with test_database.SessionLocal() as session:
        waybill = session.get(Waybill, record_ids["waybill_id"])
        waybill.status = "COMPLETED"
        session.commit()

    rows = SwitchListService.get_switch_list_rows(record_ids["operations_session_id"])

    assert rows == []


def test_setout_instruction_cannot_complete_before_pickup(test_database):
    record_ids = seed_switch_list(test_database)

    completed, message = CarMoveService.complete(record_ids["setout_id"])

    assert not completed
    assert "until the PICKUP" in message

    with test_database.SessionLocal() as session:
        setout = session.get(CarMove, record_ids["setout_id"])
        assert setout.status == "PENDING"


def test_pickup_then_setout_instructions_complete_in_order(test_database):
    record_ids = seed_switch_list(test_database)

    pickup_completed, pickup = CarMoveService.complete(record_ids["pickup_id"])
    setout_completed, setout = CarMoveService.complete(record_ids["setout_id"])

    assert pickup_completed, pickup
    assert setout_completed, setout

    with test_database.SessionLocal() as session:
        moves = (
            session.execute(select(CarMove).order_by(CarMove.route_sequence))
            .scalars()
            .all()
        )
        assert [move.status for move in moves] == ["COMPLETED", "COMPLETED"]
        assert all(move.completed_at is not None for move in moves)
