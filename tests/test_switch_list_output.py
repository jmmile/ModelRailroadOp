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
            active=True,
        )

        weston_track = LocationTrack(
            location_id=weston.id,
            name="Arrival",
            track_type="YARD",
            traffic_use="ARRIVAL",
            active=True,
        )

        session.add_all(
            (
                staging_track,
                weston_track,
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
            name="Switch List Test",
            session_date=date(
                2026,
                9,
                2,
            ),
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

        session.add_all(
            (
                train,
                operations_session,
                car,
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
            notes="Deliver to arrival track",
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

        session.add_all(
            (
                pickup,
                setout,
            )
        )

        session.commit()

        return {
            "operations_session_id": operations_session.id,
            "train_id": train.id,
            "waybill_id": waybill.id,
            "pickup_id": pickup.id,
            "setout_id": setout.id,
        }


def seed_multi_train_switch_list(
    test_database,
):
    """
    Create one Operations Session containing switch-list
    instructions for two different Trains.

    Each Train receives one Waybill with one PICKUP and one
    SETOUT CarMove.
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

        portland = Location(
            name="Portland",
            location_type="YARD",
            active=True,
        )

        session.add_all(
            (
                staging,
                weston,
                portland,
            )
        )

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

        portland_track = LocationTrack(
            location_id=portland.id,
            name="Arrival",
            track_type="YARD",
            traffic_use="ARRIVAL",
            active=True,
        )

        session.add_all(
            (
                staging_track,
                weston_track,
                portland_track,
            )
        )

        session.flush()

        train_255 = Train(
            number="255",
            name="Weston Traffic Inbound",
            train_type="Through Freight",
            active=True,
        )

        train_226 = Train(
            number="226",
            name="Portland Local",
            train_type="Local Freight",
            active=True,
        )

        operations_session = OperationsSession(
            name="Multi-Train Switch List Test",
            session_date=date(
                2026,
                9,
                4,
            ),
            status="PLANNED",
        )

        car_255 = Car(
            reporting_mark="SP",
            number="480567",
            owner="SP",
            car_type="Hopper Car",
            length=60,
            status="AVAILABLE",
            location="Staging Yard - Eastbound",
            operating_location_id=staging.id,
            operating_track_id=staging_track.id,
        )

        car_226 = Car(
            reporting_mark="GATX",
            number="83605",
            owner="GATX",
            car_type="Tank Car",
            length=50,
            status="AVAILABLE",
            location="Weston - Arrival",
            operating_location_id=weston.id,
            operating_track_id=weston_track.id,
        )

        session.add_all(
            (
                train_255,
                train_226,
                operations_session,
                car_255,
                car_226,
            )
        )

        session.flush()

        waybill_255 = Waybill(
            car_id=car_255.id,
            operations_session_id=operations_session.id,
            origin_location="Staging Yard",
            origin_location_id=staging.id,
            origin_location_track_id=staging_track.id,
            destination_location_id=weston.id,
            destination_location_track_id=weston_track.id,
            load_state="EMPTY",
            cargo_weight_lbs=0,
            status="ACTIVE",
            notes="Weston traffic",
        )

        waybill_226 = Waybill(
            car_id=car_226.id,
            operations_session_id=operations_session.id,
            origin_location="Weston",
            origin_location_id=weston.id,
            origin_location_track_id=weston_track.id,
            destination_location_id=portland.id,
            destination_location_track_id=portland_track.id,
            load_state="EMPTY",
            cargo_weight_lbs=0,
            status="ACTIVE",
            notes="Portland traffic",
        )

        session.add_all(
            (
                waybill_255,
                waybill_226,
            )
        )

        session.flush()

        train_255_pickup = CarMove(
            operations_session_id=operations_session.id,
            train_id=train_255.id,
            car_id=car_255.id,
            waybill_id=waybill_255.id,
            route_sequence=1,
            move_type="PICKUP",
            status="PENDING",
            origin_location="Staging Yard",
            destination_location="Weston",
        )

        train_255_setout = CarMove(
            operations_session_id=operations_session.id,
            train_id=train_255.id,
            car_id=car_255.id,
            waybill_id=waybill_255.id,
            route_sequence=2,
            move_type="SETOUT",
            status="PENDING",
            origin_location="Staging Yard",
            destination_location="Weston",
        )

        train_226_pickup = CarMove(
            operations_session_id=operations_session.id,
            train_id=train_226.id,
            car_id=car_226.id,
            waybill_id=waybill_226.id,
            route_sequence=1,
            move_type="PICKUP",
            status="PENDING",
            origin_location="Weston",
            destination_location="Portland",
        )

        train_226_setout = CarMove(
            operations_session_id=operations_session.id,
            train_id=train_226.id,
            car_id=car_226.id,
            waybill_id=waybill_226.id,
            route_sequence=2,
            move_type="SETOUT",
            status="PENDING",
            origin_location="Weston",
            destination_location="Portland",
        )

        session.add_all(
            (
                train_255_pickup,
                train_255_setout,
                train_226_pickup,
                train_226_setout,
            )
        )

        session.commit()

        return {
            "operations_session_id": operations_session.id,
            "train_255_id": train_255.id,
            "train_226_id": train_226.id,
        }


def test_switch_list_rows_contain_individual_car_move_details(
    test_database,
):
    record_ids = seed_switch_list(
        test_database
    )

    rows = (
        SwitchListService.get_switch_list_rows(
            record_ids["operations_session_id"]
        )
    )

    assert len(rows) == 2

    pickup_row = rows[0]
    setout_row = rows[1]

    assert pickup_row["car_move_id"] == record_ids["pickup_id"]
    assert pickup_row["move_type"] == "PICKUP"
    assert pickup_row["move_status"] == "PENDING"
    assert pickup_row["route_sequence"] == 1
    assert pickup_row["pickup_sequence"] == 1
    assert pickup_row["setout_sequence"] is None
    assert pickup_row["train"] == "M225 - Weston Inbound"
    assert pickup_row["car"] == "GN 33103"
    assert pickup_row["car_type"] == "Gondola"
    assert pickup_row["length"] == 45
    assert pickup_row["origin"] == "Staging Yard - Eastbound"
    assert pickup_row["destination"] == "Weston - Arrival"
    assert pickup_row["instruction_location"] == "Staging Yard - Eastbound"
    assert pickup_row["waybill_id"] == record_ids["waybill_id"]
    assert pickup_row["waybill_status"] == "ACTIVE"
    assert pickup_row["notes"] == "Deliver to arrival track"

    assert setout_row["car_move_id"] == record_ids["setout_id"]
    assert setout_row["move_type"] == "SETOUT"
    assert setout_row["move_status"] == "PENDING"
    assert setout_row["route_sequence"] == 3
    assert setout_row["pickup_sequence"] is None
    assert setout_row["setout_sequence"] == 3
    assert setout_row["train"] == "M225 - Weston Inbound"
    assert setout_row["car"] == "GN 33103"
    assert setout_row["car_type"] == "Gondola"
    assert setout_row["length"] == 45
    assert setout_row["origin"] == "Staging Yard - Eastbound"
    assert setout_row["destination"] == "Weston - Arrival"
    assert setout_row["instruction_location"] == "Weston - Arrival"
    assert setout_row["waybill_id"] == record_ids["waybill_id"]
    assert setout_row["waybill_status"] == "ACTIVE"
    assert setout_row["notes"] == "Deliver to arrival track"


def test_pickup_and_setout_helpers_return_matching_move_types(
    test_database,
):
    record_ids = seed_switch_list(
        test_database
    )

    pickup_rows = (
        SwitchListService.get_pickup_rows(
            record_ids["operations_session_id"]
        )
    )

    setout_rows = (
        SwitchListService.get_setout_rows(
            record_ids["operations_session_id"]
        )
    )

    assert len(pickup_rows) == 1
    assert len(setout_rows) == 1

    assert pickup_rows[0]["car_move_id"] == record_ids["pickup_id"]
    assert pickup_rows[0]["move_type"] == "PICKUP"

    assert setout_rows[0]["car_move_id"] == record_ids["setout_id"]
    assert setout_rows[0]["move_type"] == "SETOUT"


def test_switch_list_can_filter_one_train_from_multi_train_session(
    test_database,
):
    record_ids = seed_multi_train_switch_list(
        test_database
    )

    operations_session_id = (
        record_ids["operations_session_id"]
    )

    train_255_id = (
        record_ids["train_255_id"]
    )

    train_226_id = (
        record_ids["train_226_id"]
    )

    all_rows = (
        SwitchListService.get_switch_list_rows(
            operations_session_id
        )
    )

    train_255_rows = (
        SwitchListService.get_switch_list_rows(
            operations_session_id,
            train_id=train_255_id,
        )
    )

    train_226_rows = (
        SwitchListService.get_switch_list_rows(
            operations_session_id,
            train_id=train_226_id,
        )
    )

    assert len(all_rows) == 4
    assert len(train_255_rows) == 2
    assert len(train_226_rows) == 2

    assert {
        row["train_id"]
        for row in all_rows
    } == {
        train_255_id,
        train_226_id,
    }

    assert {
        row["train_id"]
        for row in train_255_rows
    } == {
        train_255_id,
    }

    assert {
        row["train_id"]
        for row in train_226_rows
    } == {
        train_226_id,
    }

    assert {
        row["move_type"]
        for row in train_255_rows
    } == {
        "PICKUP",
        "SETOUT",
    }

    assert {
        row["move_type"]
        for row in train_226_rows
    } == {
        "PICKUP",
        "SETOUT",
    }

    assert {
        row["car"]
        for row in train_255_rows
    } == {
        "SP 480567",
    }

    assert {
        row["car"]
        for row in train_226_rows
    } == {
        "GATX 83605",
    }


def test_completed_waybill_is_removed_from_switch_list(
    test_database,
):
    record_ids = seed_switch_list(
        test_database
    )

    with test_database.SessionLocal() as session:
        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        waybill.status = "COMPLETED"

        session.commit()

    rows = (
        SwitchListService.get_switch_list_rows(
            record_ids["operations_session_id"]
        )
    )

    assert rows == []


def test_setout_instruction_cannot_complete_before_pickup(
    test_database,
):
    record_ids = seed_switch_list(
        test_database
    )

    completed, message = (
        CarMoveService.complete(
            record_ids["setout_id"]
        )
    )

    assert not completed
    assert "until the PICKUP" in message

    with test_database.SessionLocal() as session:
        setout = session.get(
            CarMove,
            record_ids["setout_id"],
        )

        assert setout.status == "PENDING"


def test_pickup_then_setout_instructions_complete_in_order(
    test_database,
):
    record_ids = seed_switch_list(
        test_database
    )

    pickup_completed, pickup = (
        CarMoveService.complete(
            record_ids["pickup_id"]
        )
    )

    setout_completed, setout = (
        CarMoveService.complete(
            record_ids["setout_id"]
        )
    )

    assert pickup_completed, pickup
    assert setout_completed, setout

    with test_database.SessionLocal() as session:
        moves = (
            session.execute(
                select(
                    CarMove
                )
                .order_by(
                    CarMove.route_sequence
                )
            )
            .scalars()
            .all()
        )

        assert [
            move.status
            for move in moves
        ] == [
            "COMPLETED",
            "COMPLETED",
        ]

        assert all(
            move.completed_at is not None
            for move in moves
        )