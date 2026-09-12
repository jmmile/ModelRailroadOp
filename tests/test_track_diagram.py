from PySide6.QtCore import Qt

from modelrailroadops.models.car import Car
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot
from modelrailroadops.services.car_location_service import CarLocationService
from modelrailroadops.services.location_service import LocationService
from modelrailroadops.ui.widgets.track_diagram_widget import (
    EmptySpotWidget,
    TrackDiagramWidget,
)


def test_track_diagram_centers_car_type_beneath_identifier(
    qapp,
    test_database,
    monkeypatch,
):
    with test_database.SessionLocal() as session:
        location = Location(
            name="BNSF Interchange",
            location_type="INTERCHANGE",
            active=True,
        )
        session.add(location)
        session.flush()

        track = LocationTrack(
            location_id=location.id,
            name="Interchange",
            track_type="INTERCHANGE",
            traffic_use="BOTH",
            capacity=3,
            active=True,
        )
        session.add(track)
        session.flush()
        track_id = track.id

        session.add_all((
            Car(
                reporting_mark="GN",
                number="33103",
                owner="GN",
                car_type="Gondola",
                length=45,
                status="EMPTY",
                location="BNSF Interchange - Interchange",
                operating_location_id=location.id,
                operating_track_id=track.id,
            ),
            Car(
                reporting_mark="TXC",
                number="2266",
                owner="TXC",
                car_type="Boxcar",
                length=40,
                status="LOADED",
                location="BNSF Interchange - Interchange",
                operating_location_id=location.id,
                operating_track_id=track.id,
            ),
        ))
        session.commit()

    monkeypatch.setattr(
        "modelrailroadops.services.location_service.SessionLocal",
        test_database.SessionLocal,
    )
    monkeypatch.setattr(
        "modelrailroadops.services.industry_service.SessionLocal",
        test_database.SessionLocal,
    )

    widget = TrackDiagramWidget()

    assert len(widget.track_sections) == 1
    assert len(widget.car_symbols) == 2
    assert widget.diagram_tabs.count() == 1
    assert widget.diagram_tabs.tabText(0) == "General Tracks"
    assert widget.status_label.text().startswith("1 tracks | 2 cars")

    first, second = widget.car_symbols
    widget.find_car_edit.setText("2266")
    widget.find_car()
    assert widget.selected_car_id == second.car.id
    assert "Car: TXC 2266" in widget.details_label.text()
    assert first.number_label.text() == "GN 33103"
    assert first.type_label.text() == "Gondola"
    assert second.number_label.text() == "TXC 2266"
    assert second.type_label.text() == "Boxcar"
    assert first.width() == second.width()
    assert first.number_label.alignment() == Qt.AlignCenter
    assert first.type_label.alignment() == Qt.AlignCenter
    assert second.number_label.alignment() == Qt.AlignCenter
    assert second.type_label.alignment() == Qt.AlignCenter
    assert first.fill_color == "#e7f0f7"
    assert second.fill_color == "#d8c39e"
    assert "Loaded" in widget.legend_label.text()
    assert "Empty" in widget.legend_label.text()

    second.clicked.emit(second.car)
    assert "Car: TXC 2266" in widget.details_label.text()
    assert "Status: LOADED" in widget.details_label.text()
    assert "Length: 40 ft" in widget.details_label.text()
    assert widget.move_left_button.isEnabled()
    assert not widget.move_right_button.isEnabled()

    widget.move_selected_car(-1)
    assert widget.car_symbols[0].number_label.text() == "TXC 2266"
    assert widget.car_symbols[1].number_label.text() == "GN 33103"
    assert not widget.move_left_button.isEnabled()
    assert widget.move_right_button.isEnabled()
    assert not widget.mark_loaded_button.isEnabled()
    assert not widget.mark_empty_button.isEnabled()

    with test_database.SessionLocal() as session:
        reordered_car = session.get(Car, second.car.id)
        assert reordered_car.operating_track_position == 1

        arriving_car = Car(
            reporting_mark="SP",
            number="45222",
            owner="SP",
            car_type="Boxcar",
            length=50,
            status="EMPTY",
            location="Unassigned",
        )
        session.add(arriving_car)
        session.commit()
        arriving_car_id = arriving_car.id

    success, message = (
        CarLocationService.move_car_to_location_track_with_message(
            arriving_car_id,
            track_id,
        )
    )
    assert success, message

    with test_database.SessionLocal() as session:
        stored_track = session.get(LocationTrack, track_id)
        stored_track.capacity = 2
        session.commit()

    widget.refresh(force=True)
    assert widget.car_symbols[-1].number_label.text() == "SP 45222"

    with test_database.SessionLocal() as session:
        arriving_car = session.get(Car, arriving_car_id)
        assert arriving_car.operating_track_position == 3

    assert "color: #b00020" in widget.track_headings[0].styleSheet()

    widget.reorder_car_on_track(arriving_car_id, 0)
    assert widget.car_symbols[0].number_label.text() == "SP 45222"

    with test_database.SessionLocal() as session:
        ordered_cars = session.query(Car).filter_by(
            operating_track_id=track_id
        ).order_by(Car.operating_track_position).all()
        assert [car.id for car in ordered_cars] == [
            arriving_car_id,
            second.car.id,
            first.car.id,
        ]

    widget.close()


def test_track_diagram_groups_industry_tracks_by_town(
    qapp,
    test_database,
    monkeypatch,
):
    with test_database.SessionLocal() as session:
        operating_location = Location(
            name="Acme Transfer Company",
            location_type="INDUSTRY",
            active=True,
        )
        session.add(operating_location)
        session.flush()
        operating_track = LocationTrack(
            location_id=operating_location.id,
            name="Acme Siding",
            track_type="INDUSTRY",
            traffic_use="BOTH",
            capacity=2,
            active=True,
        )
        session.add(operating_track)
        session.flush()
        industry = Industry(
            name="Acme Transfer Company",
            railroad="GN",
            location="Pine Bluff",
            operating_location_id=operating_location.id,
        )
        session.add(industry)
        session.flush()
        industry_track = IndustryTrack(
            industry_id=industry.id,
            operating_track_id=operating_track.id,
            name="Warehouse Track",
        )
        session.add(industry_track)
        session.flush()
        first_spot = Spot(track_id=industry_track.id, spot_number=1)
        second_spot = Spot(track_id=industry_track.id, spot_number=2)
        session.add_all((first_spot, second_spot))
        session.flush()
        first_spot_id = first_spot.id
        session.add(Car(
            reporting_mark="GN",
            number="33103",
            owner="GN",
            car_type="Gondola",
            length=45,
            status="EMPTY",
            location="Acme Transfer Company - Warehouse Track",
            industry_id=industry.id,
            track_id=industry_track.id,
            spot_id=first_spot.id,
            operating_location_id=operating_location.id,
            operating_track_id=operating_track.id,
            operating_track_position=1,
        ))
        session.commit()

    monkeypatch.setattr(
        "modelrailroadops.services.location_service.SessionLocal",
        test_database.SessionLocal,
    )
    monkeypatch.setattr(
        "modelrailroadops.services.industry_service.SessionLocal",
        test_database.SessionLocal,
    )

    widget = TrackDiagramWidget()

    assert widget.diagram_tabs.count() == 2
    assert [
        widget.diagram_tabs.tabText(index)
        for index in range(widget.diagram_tabs.count())
    ] == ["General Tracks", "Pine Bluff"]
    assert len(widget.track_sections) == 1
    assert widget.track_headings[0].text().startswith(
        "Acme Transfer Company — Warehouse Track"
    )
    assert "1 occupied / 2 capacity / 1 available" in (
        widget.track_headings[0].text()
    )
    assert widget.car_symbols[0].number_label.text() == "GN 33103"
    assert widget.status_label.text().startswith("1 tracks | 1 cars")
    assert len(widget.track_sections[0].findChildren(EmptySpotWidget)) == 1
    empty_spot_widget = widget.empty_spot_widgets[0]
    empty_spot_widget.clicked.emit(empty_spot_widget.spot)
    assert "Empty Spot: Acme Transfer Company" in widget.details_label.text()
    assert "Requirements: Any car" in widget.details_label.text()
    assert widget.find_matching_car_button.isEnabled()
    assert not widget.move_left_button.isEnabled()

    widget.car_symbols[0].clicked.emit(widget.car_symbols[0].car)
    assert "Track Position: Spot 1" in widget.details_label.text()
    assert not widget.move_left_button.isEnabled()
    assert widget.move_right_button.isEnabled()
    assert widget.mark_loaded_button.isEnabled()
    assert not widget.mark_empty_button.isEnabled()
    assert not widget.find_matching_car_button.isEnabled()

    widget.set_selected_car_load_state("LOADED")
    assert "Status: LOADED" in widget.details_label.text()
    assert not widget.mark_loaded_button.isEnabled()
    assert widget.mark_empty_button.isEnabled()
    assert widget.car_symbols[0].fill_color == "#d8c39e"

    widget.set_selected_car_load_state("EMPTY")
    assert "Status: EMPTY" in widget.details_label.text()
    assert widget.car_symbols[0].fill_color == "#e7f0f7"

    widget.move_selected_car(1)
    assert "Track Position: Spot 2" in widget.details_label.text()
    assert widget.move_left_button.isEnabled()
    assert not widget.move_right_button.isEnabled()

    with test_database.SessionLocal() as session:
        moved_car = session.query(Car).filter_by(number="33103").one()
        moved_spot = session.get(Spot, moved_car.spot_id)
        assert moved_spot.spot_number == 2
        assert moved_car.location.endswith("Spot 2")

    widget.reorder_car_on_track(widget.car_symbols[0].car.id, 0)
    with test_database.SessionLocal() as session:
        dragged_car = session.query(Car).filter_by(number="33103").one()
        dragged_spot = session.get(Spot, dragged_car.spot_id)
        assert dragged_spot.spot_number == 1
        session.get(Spot, first_spot_id).empty_only = True
        session.commit()
        dragged_car_id = dragged_car.id

    success, message = LocationService.set_industry_car_load_state(
        dragged_car_id,
        "LOADED",
    )
    assert not success
    assert "requires an empty car" in message

    widget.close()
