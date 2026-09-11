from modelrailroadops.models.car import Car
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.services.car_service import CarService
from modelrailroadops.ui.dialogs.add_car_dialog import AddCarDialog


def test_roster_status_edit_preserves_general_track_location(
    qapp,
    test_database,
    monkeypatch,
):
    with test_database.SessionLocal() as session:
        location = Location(
            name="Weston Yard",
            location_type="YARD",
            active=True,
        )
        session.add(location)
        session.flush()

        track = LocationTrack(
            location_id=location.id,
            name="Pine Bluff Turn",
            track_type="ARRIVAL",
            traffic_use="BOTH",
            active=True,
        )
        session.add(track)
        session.flush()

        car = Car(
            reporting_mark="RPDX",
            number="8181",
            owner="RPDX",
            car_type="Tank Car",
            length=50,
            status="Empty",
            location="Weston Yard - Pine Bluff Turn",
            operating_location_id=location.id,
            operating_track_id=track.id,
            operating_track_position=1,
        )
        session.add(car)
        location_id = location.id
        track_id = track.id
        session.commit()
        car_id = car.id

    monkeypatch.setattr(
        "modelrailroadops.ui.dialogs.add_car_dialog.SessionLocal",
        test_database.SessionLocal,
    )
    monkeypatch.setattr(
        "modelrailroadops.services.car_service.SessionLocal",
        test_database.SessionLocal,
    )

    car = CarService.get_by_id(car_id)
    dialog = AddCarDialog(car=car)
    dialog.status.setCurrentText("Loaded")
    assert dialog.status.currentText() == "Loaded"
    dialog.save()
    assert dialog.result() == AddCarDialog.Accepted

    with test_database.SessionLocal() as session:
        saved_car = session.get(Car, car_id)
        assert saved_car.status == "Loaded"
        assert saved_car.location == "Weston Yard - Pine Bluff Turn"
        assert saved_car.operating_location_id == location_id
        assert saved_car.operating_track_id == track_id
        assert saved_car.operating_track_position == 1

    dialog.close()
