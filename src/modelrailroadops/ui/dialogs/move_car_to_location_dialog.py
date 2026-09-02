from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)

from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot
from modelrailroadops.services.car_location_service import CarLocationService
from modelrailroadops.services.location_service import LocationService


class MoveCarToLocationDialog(QDialog):
    """Move a car to a general railroad Location and Track."""

    def __init__(
        self,
        car_id,
        parent=None,
        assignment=False,
    ):
        super().__init__(parent)

        self.car_id = car_id
        self.assignment = assignment
        self.locations = []
        self.setWindowTitle(
            "Assign Car" if assignment else "Move Car"
        )
        self.resize(500, 260)

        layout = QVBoxLayout(self)
        self.car_label = QLabel()
        layout.addWidget(self.car_label)

        form = QFormLayout()
        self.location_combo = QComboBox()
        self.track_combo = QComboBox()
        self.spot_combo = QComboBox()

        form.addRow("Destination Location:", self.location_combo)
        form.addRow("Destination Track:", self.track_combo)
        form.addRow("Destination Spot:", self.spot_combo)
        layout.addLayout(form)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.buttons.button(QDialogButtonBox.Save).setText(
            "Assign" if assignment else "Move"
        )
        self.buttons.accepted.connect(self.move_car)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.location_combo.currentIndexChanged.connect(self.load_tracks)
        self.track_combo.currentIndexChanged.connect(self.load_spots)

        self.load_car()
        self.load_locations()

    def load_car(self):
        with SessionLocal() as session:
            car = session.get(Car, self.car_id)
            if car is None:
                self.car_label.setText("Car not found")
                self.buttons.setEnabled(False)
                return
            action = "Assign" if self.assignment else "Move"
            self.car_label.setText(
                f"{action}: {car.reporting_mark} {car.number}"
            )

    def load_locations(self):
        self.location_combo.blockSignals(True)
        self.location_combo.clear()
        self.locations = [
            location
            for location in LocationService.get_all()
            if location.active and any(track.active for track in location.tracks)
        ]

        for location in self.locations:
            self.location_combo.addItem(
                f"{location.name} — {location.location_type.title()}",
                location.id,
            )

        self.location_combo.blockSignals(False)
        self.load_tracks()

    def selected_location(self):
        location_id = self.location_combo.currentData()
        return next(
            (item for item in self.locations if item.id == location_id),
            None,
        )

    def load_tracks(self):
        self.track_combo.blockSignals(True)
        self.track_combo.clear()
        location = self.selected_location()

        if location is not None:
            for track in location.tracks:
                if track.active:
                    self.track_combo.addItem(
                        (
                            f"{track.name} — {track.track_type.title()}"
                            f" / {track.traffic_use.title()}"
                        ),
                        track.id,
                    )

        self.track_combo.blockSignals(False)
        self.load_spots()

    def load_spots(self):
        self.spot_combo.clear()
        track_id = self.track_combo.currentData()

        if track_id is None:
            self.spot_combo.setEnabled(False)
            self.update_move_button()
            return

        with SessionLocal() as session:
            industry_track = (
                session.execute(
                    select(IndustryTrack).where(
                        IndustryTrack.operating_track_id == track_id
                    )
                )
                .scalars()
                .first()
            )

            if industry_track is None:
                self.spot_combo.addItem("Not required", None)
                self.spot_combo.setEnabled(False)
                self.update_move_button()
                return

            occupied_spot_ids = {
                value
                for value in session.execute(
                    select(Car.spot_id).where(
                        Car.spot_id.isnot(None),
                        Car.id != self.car_id,
                    )
                ).scalars()
            }

            spots = (
                session.execute(
                    select(Spot)
                    .where(Spot.track_id == industry_track.id)
                    .order_by(Spot.spot_number)
                )
                .scalars()
                .all()
            )

            for spot in spots:
                if spot.id not in occupied_spot_ids:
                    self.spot_combo.addItem(
                        f"Spot {spot.spot_number}",
                        spot.id,
                    )

        self.spot_combo.setEnabled(True)
        self.update_move_button()

    def update_move_button(self):
        enabled = self.track_combo.currentData() is not None

        if self.spot_combo.isEnabled():
            enabled = enabled and self.spot_combo.currentData() is not None

        self.buttons.button(QDialogButtonBox.Save).setEnabled(enabled)

    def move_car(self):
        spot_id = self.spot_combo.currentData()

        if self.spot_combo.isEnabled():
            success, message = (
                CarLocationService.assign_car_to_spot_with_message(
                    self.car_id,
                    spot_id,
                )
            )
        else:
            success, message = (
                CarLocationService.move_car_to_location_track_with_message(
                    self.car_id,
                    self.track_combo.currentData(),
                )
            )

        if not success:
            title = "Assign Car" if self.assignment else "Move Car"
            fallback = "Assignment failed." if self.assignment else "Move failed."
            QMessageBox.warning(self, title, message or fallback)
            return

        self.accept()
