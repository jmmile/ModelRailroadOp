from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.industry_demand_service import (
    IndustryDemandService,
)


def test_industry_demand_matches_car_and_generates_waybill(
    test_database,
    monkeypatch,
):
    monkeypatch.setattr(
        "modelrailroadops.services.industry_demand_service.SessionLocal",
        test_database.SessionLocal,
    )
    monkeypatch.setattr(
        "modelrailroadops.services.waybill_service.SessionLocal",
        test_database.SessionLocal,
    )

    with test_database.SessionLocal() as session:
        yard = Location(name="Yard", location_type="YARD", active=True)
        industry_location = Location(
            name="Acme", location_type="INDUSTRY", active=True
        )
        session.add_all((yard, industry_location))
        session.flush()
        yard_track = LocationTrack(
            location_id=yard.id,
            name="Track 1",
            track_type="YARD",
            traffic_use="BOTH",
            capacity=4,
            active=True,
        )
        operating_track = LocationTrack(
            location_id=industry_location.id,
            name="Siding",
            track_type="INDUSTRY",
            traffic_use="BOTH",
            capacity=1,
            active=True,
        )
        session.add_all((yard_track, operating_track))
        session.flush()
        industry = Industry(
            name="Acme",
            railroad="GN",
            location="Pine Bluff",
            operating_location_id=industry_location.id,
        )
        session.add(industry)
        session.flush()
        industry_track = IndustryTrack(
            industry_id=industry.id,
            operating_track_id=operating_track.id,
            name="Dock",
        )
        session.add(industry_track)
        session.flush()
        spot = Spot(
            track_id=industry_track.id,
            spot_number=1,
            allowed_car_type="Boxcar",
            empty_only=True,
        )
        car = Car(
            reporting_mark="GN",
            number="100",
            owner="GN",
            car_type="Boxcar",
            length=40,
            status="EMPTY",
            location="Yard - Track 1",
            operating_location_id=yard.id,
            operating_track_id=yard_track.id,
        )
        session.add_all((spot, car))
        session.commit()
        spot_id = spot.id
        car_id = car.id

    demands = IndustryDemandService.get_open_demands()
    assert len(demands) == 1
    assert demands[0]["town"] == "Pine Bluff"
    assert demands[0]["requirements"] == "Boxcar, Empty"
    assert demands[0]["matches"] == [{
        "id": car_id,
        "name": "GN 100",
        "car_type": "Boxcar",
        "status": "EMPTY",
        "location": "Yard - Track 1",
    }]

    success, result = IndustryDemandService.create_waybill(spot_id, car_id)
    assert success, result

    with test_database.SessionLocal() as session:
        waybill = session.query(Waybill).one()
        assert waybill.car_id == car_id
        assert waybill.destination_spot_id == spot_id
        assert waybill.load_state == "EMPTY"

    assert IndustryDemandService.get_open_demands() == []
