from datetime import date

import pytest

from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot

from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack

from modelrailroadops.models.car import Car
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.operations_session_train import OperationsSessionTrain
from modelrailroadops.models.train import Train
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services import industry_demand_service
from modelrailroadops.services.dashboard_service import DashboardService
from modelrailroadops.ui.widgets.dashboard_widget import DashboardWidget


def test_capacity_thresholds(test_database, monkeypatch):
    monkeypatch.setattr(
        industry_demand_service, "SessionLocal", test_database.SessionLocal
    )
    with test_database.SessionLocal() as session:
        location = Location(name="Yard", location_type="YARD")
        session.add(location)
        session.flush()
        for capacity in (None, 0, 4, 5, 6):
            track = LocationTrack(
                location_id=location.id, name=str(capacity), capacity=capacity
            )
            session.add(track)
            session.flush()
            for number in range(4):
                session.add(
                    Car(
                        reporting_mark="TEST",
                        number=f"{capacity}-{number}",
                        owner="TEST",
                        car_type="Boxcar",
                        status="Empty",
                        location="Yard",
                        operating_location_id=location.id,
                        operating_track_id=track.id,
                    )
                )
        session.commit()
    rows = {
        row["track"]: row for row in DashboardService.get_summary()["capacity_details"]
    }
    assert rows["None"]["status"] == "Capacity not set"
    assert rows["0"]["status"] == "Over capacity"
    assert rows["4"]["status"] == "Full"
    assert rows["5"]["status"] == "Near capacity"
    assert rows["6"]["status"] == "Available"


@pytest.mark.parametrize("manual_capacity", [None, 99])
def test_industry_capacity_uses_defined_spots(test_database, monkeypatch, manual_capacity):
    monkeypatch.setattr(industry_demand_service, "SessionLocal", test_database.SessionLocal)
    with test_database.SessionLocal() as session:
        location = Location(name="Acme", location_type="INDUSTRY")
        session.add(location)
        session.flush()
        track = LocationTrack(location_id=location.id, name="Dock", capacity=manual_capacity)
        industry = Industry(name="Acme", railroad="GN", location="Town", operating_location_id=location.id)
        session.add_all([track, industry])
        session.flush()
        industry_track = IndustryTrack(industry_id=industry.id, name="Dock", operating_track_id=track.id)
        session.add(industry_track)
        session.flush()
        session.add_all([Spot(track_id=industry_track.id, spot_number=n) for n in (1, 2, 3)])
        session.commit()
    row = DashboardService.get_summary()["capacity_details"][0]
    assert row["capacity"] == 3
    assert row["available"] == 3
    assert row["status"] == "Available"


def _seed_dashboard(test_database, monkeypatch):
    monkeypatch.setattr(
        industry_demand_service,
        "SessionLocal",
        test_database.SessionLocal,
    )

    with test_database.SessionLocal() as session:
        operations_session = OperationsSession(
            name="Saturday Session",
            session_date=date(2026, 9, 13),
            status="ACTIVE",
        )
        train = Train(
            number="201",
            name="Pine Bluff Turn",
            train_type="Local Freight",
        )
        car = Car(
            reporting_mark="GN",
            number="33103",
            owner="GN",
            car_type="Boxcar",
            status="LOADED",
            location="On Train: L201 - Pine Bluff Turn",
        )
        session.add_all((operations_session, train, car))
        session.flush()
        assignment = OperationsSessionTrain(
            operations_session_id=operations_session.id,
            train_id=train.id,
        )
        waybill = Waybill(
            car_id=car.id,
            operations_session_id=operations_session.id,
            origin_location="Weston Yard",
            status="IN_PROGRESS",
        )
        session.add_all((assignment, waybill))
        session.flush()
        pickup = CarMove(
            operations_session_id=operations_session.id,
            train_id=train.id,
            car_id=car.id,
            waybill_id=waybill.id,
            move_type="PICKUP",
            status="COMPLETED",
        )
        setout = CarMove(
            operations_session_id=operations_session.id,
            train_id=train.id,
            car_id=car.id,
            waybill_id=waybill.id,
            move_type="SETOUT",
            status="PENDING",
        )
        session.add_all((pickup, setout))
        session.commit()


def test_dashboard_summary_reports_current_operations(
    test_database,
    monkeypatch,
):
    _seed_dashboard(test_database, monkeypatch)

    summary = DashboardService.get_summary()

    assert summary["current_operations"]["name"] == "Saturday Session"
    assert summary["current_operations"]["trains"] == "L201 - Pine Bluff Turn"
    assert summary["current_operations"]["completed_moves"] == 1
    assert summary["current_operations"]["total_moves"] == 2
    assert summary["current_operations"]["progress"] == 50
    assert summary["fleet"]["total"] == 1
    assert summary["fleet"]["loaded"] == 1
    assert summary["fleet"]["on_train"] == 1
    assert summary["work_waiting"]["active_waybills"] == 1
    assert summary["work_waiting"]["pending_moves"] == 1


def test_dashboard_widget_displays_summary(
    qapp,
    test_database,
    monkeypatch,
):
    _seed_dashboard(test_database, monkeypatch)

    widget = DashboardWidget()

    assert "Saturday Session" in widget.session_label.text()
    assert "1 of 2" in widget.session_detail_label.text()
    assert widget.session_progress.value() == 50
    assert "Total freight cars: 1" in widget.fleet_label.text()
    assert "Pending switch-list moves: 1" in widget.work_label.text()
    widget.close()
