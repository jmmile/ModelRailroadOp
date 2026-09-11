from modelrailroadops.models.car import Car
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.ui.widgets.locations_widget import LocationsWidget


def test_locations_tab_shows_general_track_occupancy(
    qapp,
    test_database,
    monkeypatch,
):
    with test_database.SessionLocal() as session:
        location = Location(
            name="Staging Yard",
            location_type="STAGING",
            active=True,
        )
        session.add(location)
        session.flush()

        track = LocationTrack(
            location_id=location.id,
            name="East Bound Track",
            track_type="DEPARTURE",
            traffic_use="OUTBOUND",
            capacity=3,
            active=True,
        )
        session.add(track)
        session.flush()

        session.add_all(
            (
                Car(
                    reporting_mark="GN",
                    number="33103",
                    owner="GN",
                    car_type="Boxcar",
                    length=40,
                    status="EMPTY",
                    location="Staging Yard - East Bound Track",
                    operating_location_id=location.id,
                    operating_track_id=track.id,
                ),
                Car(
                    reporting_mark="SP",
                    number="45222",
                    owner="SP",
                    car_type="Boxcar",
                    length=50,
                    status="LOADED",
                    location="Staging Yard - East Bound Track",
                    operating_location_id=location.id,
                    operating_track_id=track.id,
                ),
            )
        )
        session.commit()

    monkeypatch.setattr(
        "modelrailroadops.services.location_service.SessionLocal",
        test_database.SessionLocal,
    )

    widget = LocationsWidget()
    widget.location_table.selectRow(0)
    widget.track_table.selectRow(0)

    assert widget.track_model.item(0, 0).text() == "East Bound Track"
    assert widget.track_model.item(0, 3).text() == "3"
    assert widget.track_model.item(0, 4).text() == "2"
    assert widget.track_model.item(0, 5).text() == "1"
    assert widget.track_cars_label.text() == "Cars on East Bound Track: 2"
    assert widget.track_car_model.rowCount() == 2
    assert widget.track_car_model.item(0, 0).text() == "GN 33103"
    assert (
        widget.track_car_model.item(0, 4).text()
        == "Staging Yard - East Bound Track"
    )

    widget.close()
