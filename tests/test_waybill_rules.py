from datetime import date

from sqlalchemy import func, select

from modelrailroadops.models.car import Car
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.waybill_service import WaybillService


def test_car_cannot_receive_two_unfinished_waybills(test_database):
    with test_database.SessionLocal() as session:
        source = Location(
            name="Staging",
            location_type="STAGING",
            active=True,
        )
        destination = Location(
            name="Weston Yard",
            location_type="YARD",
            active=True,
        )
        session.add_all((source, destination))
        session.flush()

        source_track = LocationTrack(
            location_id=source.id,
            name="Departure",
            track_type="STAGING",
            traffic_use="DEPARTURE",
            active=True,
        )
        destination_track = LocationTrack(
            location_id=destination.id,
            name="Arrival",
            track_type="YARD",
            traffic_use="ARRIVAL",
            active=True,
        )
        session.add_all((source_track, destination_track))
        session.flush()

        car = Car(
            reporting_mark="TEST",
            number="2002",
            owner="Test Railroad",
            car_type="Boxcar",
            status="AVAILABLE",
            location="Staging - Departure",
            operating_location_id=source.id,
            operating_track_id=source_track.id,
        )
        operations_session = OperationsSession(
            name="Duplicate Waybill Test",
            session_date=date(2026, 9, 1),
            status="PLANNED",
        )
        session.add_all((car, operations_session))
        session.commit()

        values = {
            "car_id": car.id,
            "operations_session_id": operations_session.id,
            "source_id": source.id,
            "source_track_id": source_track.id,
            "destination_id": destination.id,
            "destination_track_id": destination_track.id,
        }

    created, first_waybill = WaybillService.create(
        car_id=values["car_id"],
        operations_session_id=values["operations_session_id"],
        origin_location="Staging",
        destination_industry_id=None,
        destination_track_id=None,
        destination_spot_id=None,
        origin_location_id=values["source_id"],
        origin_location_track_id=values["source_track_id"],
        destination_location_id=values["destination_id"],
        destination_location_track_id=values["destination_track_id"],
        load_state="EMPTY",
    )
    assert created, first_waybill

    created, message = WaybillService.create(
        car_id=values["car_id"],
        operations_session_id=values["operations_session_id"],
        origin_location="Staging",
        destination_industry_id=None,
        destination_track_id=None,
        destination_spot_id=None,
        origin_location_id=values["source_id"],
        origin_location_track_id=values["source_track_id"],
        destination_location_id=values["destination_id"],
        destination_location_track_id=values["destination_track_id"],
        load_state="EMPTY",
    )

    assert not created
    assert "already has an unfinished waybill" in message

    with test_database.SessionLocal() as session:
        waybill_count = session.scalar(select(func.count()).select_from(Waybill))
        assert waybill_count == 1

def test_completed_waybill_can_be_archived_and_restored(test_database):
    with test_database.SessionLocal() as session:
        car = Car(
            reporting_mark="TEST",
            number="3001",
            owner="Test Railroad",
            car_type="Boxcar",
            status="AVAILABLE",
            location="Test Location",
        )

        waybill = Waybill(
            car=car,
            origin_location="Test Origin",
            status="COMPLETED",
            completed_at=date(2026, 9, 1),
        )

        session.add(waybill)
        session.commit()

        waybill_id = waybill.id

    success, archived_waybill = WaybillService.archive(
        waybill_id
    )

    assert success
    assert archived_waybill.archived is True
    assert archived_waybill.archived_at is not None
    assert archived_waybill.status == "COMPLETED"

    success, restored_waybill = WaybillService.restore_from_archive(
        waybill_id
    )

    assert success
    assert restored_waybill.archived is False
    assert restored_waybill.archived_at is None
    assert restored_waybill.status == "COMPLETED"


def test_unfinished_waybill_cannot_be_archived(test_database):
    with test_database.SessionLocal() as session:
        car = Car(
            reporting_mark="TEST",
            number="3002",
            owner="Test Railroad",
            car_type="Boxcar",
            status="AVAILABLE",
            location="Test Location",
        )

        waybill = Waybill(
            car=car,
            origin_location="Test Origin",
            status="ACTIVE",
        )

        session.add(waybill)
        session.commit()

        waybill_id = waybill.id

    success, message = WaybillService.archive(
        waybill_id
    )

    assert not success
    assert message == "Only a completed waybill can be archived."


def test_archive_rejects_already_archived_waybill(test_database):
    with test_database.SessionLocal() as session:
        car = Car(
            reporting_mark="TEST",
            number="3003",
            owner="Test Railroad",
            car_type="Boxcar",
            status="AVAILABLE",
            location="Test Location",
        )

        waybill = Waybill(
            car=car,
            origin_location="Test Origin",
            status="COMPLETED",
        )

        session.add(waybill)
        session.commit()

        waybill_id = waybill.id

    success, result = WaybillService.archive(
        waybill_id
    )
    assert success, result

    success, message = WaybillService.archive(
        waybill_id
    )

    assert not success
    assert message == "Waybill is already archived."


def test_restore_rejects_non_archived_waybill(test_database):
    with test_database.SessionLocal() as session:
        car = Car(
            reporting_mark="TEST",
            number="3004",
            owner="Test Railroad",
            car_type="Boxcar",
            status="AVAILABLE",
            location="Test Location",
        )

        waybill = Waybill(
            car=car,
            origin_location="Test Origin",
            status="COMPLETED",
        )

        session.add(waybill)
        session.commit()

        waybill_id = waybill.id

    success, message = WaybillService.restore_from_archive(
        waybill_id
    )

    assert not success
    assert message == "Waybill is not archived."

