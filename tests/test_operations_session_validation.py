from datetime import date

from modelrailroadops.models.car import Car
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.services.operations_session_service import (
    OperationsSessionService,
)


def test_pre_session_validation_reports_readiness_problems(
    test_database,
):
    with test_database.SessionLocal() as session:
        operations_session = OperationsSession(
            name="Test Session",
            session_date=date(2026, 9, 11),
            status="PLANNED",
        )
        location = Location(
            name="Test Yard",
            location_type="YARD",
            active=True,
        )
        session.add_all((operations_session, location))
        session.flush()
        session_id = operations_session.id
        track = LocationTrack(
            location_id=location.id,
            name="Yard Track",
            track_type="YARD",
            traffic_use="BOTH",
            capacity=1,
            active=True,
        )
        session.add(track)
        session.flush()
        session.add_all((
            Car(
                reporting_mark="GN",
                number="1",
                owner="GN",
                car_type="Boxcar",
                length=40,
                status="EMPTY",
                location="Test Yard - Yard Track",
                operating_location_id=location.id,
                operating_track_id=track.id,
            ),
            Car(
                reporting_mark="GN",
                number="2",
                owner="GN",
                car_type="Boxcar",
                length=40,
                status="EMPTY",
                location="Test Yard - Yard Track",
                operating_location_id=location.id,
                operating_track_id=track.id,
            ),
        ))
        session.commit()

    ready, report = OperationsSessionService.validate_pre_session(session_id)

    assert not ready
    errors = " ".join(report["errors"])
    warnings = " ".join(report["warnings"])
    assert "No trains are assigned" in errors
    assert "over capacity" in errors
    assert "No non-archived waybills" in warnings
    assert report["session_name"] == "Test Session"


def test_pre_session_validation_does_not_change_session_status(
    test_database,
):
    with test_database.SessionLocal() as session:
        operations_session = OperationsSession(
            name="Read Only Check",
            session_date=date(2026, 9, 11),
            status="PLANNED",
        )
        session.add(operations_session)
        session.commit()
        session_id = operations_session.id

    OperationsSessionService.validate_pre_session(session_id)

    with test_database.SessionLocal() as session:
        stored = session.get(OperationsSession, session_id)
        assert stored.status == "PLANNED"
