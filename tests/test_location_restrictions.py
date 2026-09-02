from datetime import date

import pytest
from sqlalchemy import func, select

from modelrailroadops.models.car import Car
from modelrailroadops.models.car_movement import CarMovement
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.spot import Spot
from modelrailroadops.services.car_location_service import CarLocationService


@pytest.mark.parametrize(
    ("car_values", "spot_values", "expected_message"),
    (
        ({"car_type": "Boxcar"}, {"allowed_car_type": "Tank Car"}, "Car type"),
        ({"owner": "UP"}, {"allowed_owner": "BNSF"}, "Car owner"),
        ({"length": 60}, {"max_length": 50}, "length exceeds"),
        ({"hazardous": True}, {"hazardous_allowed": False}, "Hazardous"),
        ({"status": "EMPTY"}, {"load_only": True}, "loaded car"),
        ({"status": "LOADED"}, {"empty_only": True}, "empty car"),
    ),
)
def test_spot_restrictions_reject_ineligible_car(
    car_values,
    spot_values,
    expected_message,
):
    car_defaults = {
        "reporting_mark": "TEST",
        "number": "4004",
        "owner": "Test Railroad",
        "car_type": "Boxcar",
        "length": 50,
        "status": "EMPTY",
        "location": "Unassigned",
    }
    hazardous = car_values.pop("hazardous", False)
    car_defaults.update(car_values)
    car = Car(**car_defaults)
    car.hazardous = hazardous

    spot_defaults = {
        "track_id": 1,
        "spot_number": 1,
        "hazardous_allowed": True,
        "load_only": False,
        "empty_only": False,
    }
    spot_defaults.update(spot_values)
    spot = Spot(**spot_defaults)

    valid, message = CarLocationService.validate_car_for_spot(car, spot)

    assert not valid
    assert expected_message.casefold() in message.casefold()


def test_eligible_car_passes_all_spot_restrictions():
    car = Car(
        reporting_mark="BNSF",
        number="5005",
        owner="BNSF",
        car_type="Tank Car",
        length=50,
        status="LOADED",
        location="Unassigned",
    )
    car.hazardous = False
    spot = Spot(
        track_id=1,
        spot_number=1,
        allowed_car_type="Tank Car",
        allowed_owner="BNSF",
        max_length=50,
        hazardous_allowed=False,
        load_only=True,
        empty_only=False,
    )

    valid, message = CarLocationService.validate_car_for_spot(car, spot)

    assert valid, message


def test_general_track_capacity_blocks_an_additional_car(test_database):
    with test_database.SessionLocal() as session:
        location = Location(
            name="Weston Yard",
            location_type="YARD",
            active=True,
        )
        operations_session = OperationsSession(
            name="Capacity Test",
            session_date=date(2026, 9, 1),
            status="PLANNED",
        )
        session.add_all((location, operations_session))
        session.flush()

        track = LocationTrack(
            location_id=location.id,
            name="Arrival",
            track_type="YARD",
            traffic_use="ARRIVAL",
            capacity=1,
            active=True,
        )
        session.add(track)
        session.flush()

        occupying_car = Car(
            reporting_mark="TEST",
            number="6006",
            owner="Test Railroad",
            car_type="Boxcar",
            status="AVAILABLE",
            location="Weston Yard - Arrival",
            operating_location_id=location.id,
            operating_track_id=track.id,
        )
        arriving_car = Car(
            reporting_mark="TEST",
            number="7007",
            owner="Test Railroad",
            car_type="Boxcar",
            status="AVAILABLE",
            location="Staging",
        )
        session.add_all((occupying_car, arriving_car))
        session.commit()

        values = {
            "track_id": track.id,
            "arriving_car_id": arriving_car.id,
            "operations_session_id": operations_session.id,
        }

    moved, message = CarLocationService.move_car_to_location_track_with_message(
        values["arriving_car_id"],
        values["track_id"],
        values["operations_session_id"],
    )

    assert not moved
    assert "capacity" in message.casefold()

    with test_database.SessionLocal() as session:
        operations_session = session.get(
            OperationsSession,
            values["operations_session_id"],
        )
        movement_count = session.scalar(select(func.count()).select_from(CarMovement))
        assert operations_session.status == "PLANNED"
        assert movement_count == 0
