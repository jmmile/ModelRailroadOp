from datetime import date

from sqlalchemy import func, select

from modelrailroadops.models.car import Car
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.operations_session_train import OperationsSessionTrain
from modelrailroadops.models.train import Train
from modelrailroadops.models.train_route import TrainRoute
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.car_move_generation_service import (
    CarMoveGenerationService,
)


def seed_route_scenario(
    test_database,
    *,
    destination_on_route=True,
    reverse_route=False,
    destination_track_on_route=True,
    operations_session_status="PLANNED",
):
    """Create one assigned train and one waybill for route-generation tests."""

    with test_database.SessionLocal() as session:
        staging = Location(
            name="Staging Yard",
            location_type="STAGING",
            active=True,
        )
        pine_bluff = Location(
            name="Pine Bluff",
            location_type="TOWN",
            active=True,
        )
        weston = Location(
            name="Weston",
            location_type="YARD",
            active=True,
        )
        devin = Location(
            name="Devin",
            location_type="TOWN",
            active=True,
        )
        session.add_all((staging, pine_bluff, weston, devin))
        session.flush()

        staging_track = LocationTrack(
            location_id=staging.id,
            name="Eastbound",
            track_type="STAGING",
            traffic_use="BOTH",
            active=True,
        )
        pine_bluff_track = LocationTrack(
            location_id=pine_bluff.id,
            name="Main",
            track_type="MAIN",
            traffic_use="BOTH",
            active=True,
        )
        weston_arrival = LocationTrack(
            location_id=weston.id,
            name="Arrival",
            track_type="YARD",
            traffic_use="ARRIVAL",
            active=True,
        )
        weston_classification = LocationTrack(
            location_id=weston.id,
            name="Classification",
            track_type="YARD",
            traffic_use="BOTH",
            active=True,
        )
        devin_track = LocationTrack(
            location_id=devin.id,
            name="Siding",
            track_type="SIDING",
            traffic_use="BOTH",
            active=True,
        )
        session.add_all(
            (
                staging_track,
                pine_bluff_track,
                weston_arrival,
                weston_classification,
                devin_track,
            )
        )
        session.flush()

        train = Train(
            number="225",
            name="Weston Inbound",
            train_type="Through Freight",
            active=True,
        )
        operations_session = OperationsSession(
            name="Weston Inbound",
            session_date=date(2026, 9, 1),
            status=operations_session_status,
        )
        car = Car(
            reporting_mark="TEST",
            number="3003",
            owner="Test Railroad",
            car_type="Boxcar",
            status="AVAILABLE",
            location="Staging Yard - Eastbound",
            operating_location_id=staging.id,
            operating_track_id=staging_track.id,
        )
        session.add_all((train, operations_session, car))
        session.flush()

        if reverse_route:
            staging_sequence, destination_sequence = 3, 1
        else:
            staging_sequence, destination_sequence = 1, 3

        destination_location = weston if destination_on_route else devin
        destination_track = weston_arrival if destination_on_route else devin_track
        route_destination_track = (
            weston_arrival if destination_track_on_route else weston_classification
        )

        session.add_all(
            (
                OperationsSessionTrain(
                    operations_session_id=operations_session.id,
                    train_id=train.id,
                ),
                TrainRoute(
                    train_id=train.id,
                    sequence=staging_sequence,
                    location=staging.name,
                    location_id=staging.id,
                    location_track_id=staging_track.id,
                ),
                TrainRoute(
                    train_id=train.id,
                    sequence=2,
                    location=pine_bluff.name,
                    location_id=pine_bluff.id,
                    location_track_id=pine_bluff_track.id,
                ),
                TrainRoute(
                    train_id=train.id,
                    sequence=destination_sequence,
                    location=weston.name,
                    location_id=weston.id,
                    location_track_id=route_destination_track.id,
                ),
            )
        )

        waybill = Waybill(
            car_id=car.id,
            operations_session_id=operations_session.id,
            origin_location=staging.name,
            origin_location_id=staging.id,
            origin_location_track_id=staging_track.id,
            destination_location_id=destination_location.id,
            destination_location_track_id=destination_track.id,
            load_state="EMPTY",
            cargo_weight_lbs=0,
            status="ACTIVE",
        )
        session.add(waybill)
        session.commit()

        return {
            "operations_session_id": operations_session.id,
            "train_id": train.id,
            "waybill_id": waybill.id,
        }


def test_matching_route_generates_pickup_and_setout(test_database):
    record_ids = seed_route_scenario(test_database)

    success, result = CarMoveGenerationService.generate(
        record_ids["operations_session_id"]
    )

    assert success
    assert result["generated"] == 2
    assert result["skipped"] == 0

    with test_database.SessionLocal() as session:
        moves = (
            session.execute(
                select(CarMove).order_by(CarMove.route_sequence, CarMove.id)
            )
            .scalars()
            .all()
        )

        assert [move.move_type for move in moves] == ["PICKUP", "SETOUT"]
        assert [move.route_sequence for move in moves] == [1, 3]
        assert all(move.status == "PENDING" for move in moves)
        assert all(move.train_id == record_ids["train_id"] for move in moves)
        assert all(move.waybill_id == record_ids["waybill_id"] for move in moves)


def test_regenerating_does_not_duplicate_existing_moves(test_database):
    record_ids = seed_route_scenario(test_database)

    first_success, first_result = CarMoveGenerationService.generate(
        record_ids["operations_session_id"]
    )
    second_success, second_result = CarMoveGenerationService.generate(
        record_ids["operations_session_id"]
    )

    assert first_success
    assert first_result["generated"] == 2
    assert second_success
    assert second_result["generated"] == 0
    assert second_result["skipped"] == 1
    assert "already has Car Moves" in second_result["messages"][0]

    with test_database.SessionLocal() as session:
        move_count = session.scalar(select(func.count()).select_from(CarMove))
        assert move_count == 2


def test_waybill_without_matching_destination_is_skipped(test_database):
    record_ids = seed_route_scenario(test_database, destination_on_route=False)

    success, result = CarMoveGenerationService.generate(
        record_ids["operations_session_id"]
    )

    assert success
    assert result["generated"] == 0
    assert result["skipped"] == 1
    assert "No assigned train has a route" in result["messages"][0]

    with test_database.SessionLocal() as session:
        move_count = session.scalar(select(func.count()).select_from(CarMove))
        assert move_count == 0


def test_route_must_visit_origin_before_destination(test_database):
    record_ids = seed_route_scenario(test_database, reverse_route=True)

    success, result = CarMoveGenerationService.generate(
        record_ids["operations_session_id"]
    )

    assert success
    assert result["generated"] == 0
    assert result["skipped"] == 1
    assert "No assigned train has a route" in result["messages"][0]


def test_structured_track_must_match_route_track(test_database):
    record_ids = seed_route_scenario(
        test_database,
        destination_track_on_route=False,
    )

    success, result = CarMoveGenerationService.generate(
        record_ids["operations_session_id"]
    )

    assert success
    assert result["generated"] == 0
    assert result["skipped"] == 1
    assert "No assigned train has a route" in result["messages"][0]


def test_terminal_session_cannot_generate_moves(test_database):
    record_ids = seed_route_scenario(
        test_database,
        operations_session_status="COMPLETED",
    )

    success, result = CarMoveGenerationService.generate(
        record_ids["operations_session_id"]
    )

    assert not success
    assert result["generated"] == 0
    assert "completed Operations Session" in result["messages"][0]
