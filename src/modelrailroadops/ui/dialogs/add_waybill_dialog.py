from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)
from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.location_service import LocationService
from modelrailroadops.services.waybill_service import WaybillService
from modelrailroadops.ui.waybills.waybill_form import WaybillFormRenderer


class AddWaybillDialog(QDialog):
    """Create or edit a Location/Track based Waybill."""

    def __init__(self, parent=None, waybill=None):
        super().__init__(parent)

        self.waybill = waybill
        self.locations = []
        self.loading_existing = False

        self.setWindowTitle("Add Waybill" if waybill is None else "Edit Waybill")
        self.resize(620, 960)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.car_combo = QComboBox()
        self.car_type_label = QLabel("—")
        self.car_image_label = QLabel("Select a car to preview its picture.")
        self.car_image_label.setAlignment(Qt.AlignCenter)
        self.car_image_label.setFixedSize(340, 160)
        self.car_image_label.setStyleSheet(
            "QLabel { background-color: white; border: 1px solid #b8b8b8; }"
        )
        self.operations_session_combo = QComboBox()
        self.origin_location_combo = QComboBox()
        self.origin_track_combo = QComboBox()
        self.origin_spot_combo = QComboBox()
        self.destination_location_combo = QComboBox()
        self.destination_track_combo = QComboBox()
        self.destination_spot_combo = QComboBox()

        for combo in (
            self.car_combo,
            self.operations_session_combo,
            self.origin_location_combo,
            self.origin_track_combo,
            self.origin_spot_combo,
            self.destination_location_combo,
            self.destination_track_combo,
            self.destination_spot_combo,
        ):
            combo.setMinimumWidth(340)

        form.addRow("Car:", self.car_combo)
        form.addRow("Car Type:", self.car_type_label)
        form.addRow("Operations Session:", self.operations_session_combo)
        form.addRow("Origin Location:", self.origin_location_combo)
        form.addRow("Origin Track:", self.origin_track_combo)
        form.addRow("Origin Spot:", self.origin_spot_combo)
        form.addRow("Destination Location:", self.destination_location_combo)
        form.addRow("Destination Track:", self.destination_track_combo)
        form.addRow("Destination Spot:", self.destination_spot_combo)
        layout.addLayout(form)

        load_group = QGroupBox("Load and Weight")
        load_form = QFormLayout(load_group)
        self.empty_weight_label = QLabel("Not entered")
        self.load_limit_label = QLabel("Not entered")
        self.load_state_combo = QComboBox()
        self.load_state_combo.addItem("Select loaded or empty", None)
        self.load_state_combo.addItem("Loaded", "LOADED")
        self.load_state_combo.addItem("Empty", "EMPTY")
        self.commodity_edit = QLineEdit()
        self.commodity_edit.setPlaceholderText("Optional commodity")
        self.cargo_weight_edit = QLineEdit()
        self.cargo_weight_edit.setPlaceholderText("Cargo weight in pounds")
        self.gross_weight_label = QLabel("Not calculated")
        self.tonnage_label = QLabel("Not calculated")
        load_form.addRow("Car Empty Weight:", self.empty_weight_label)
        load_form.addRow("Car Load Limit:", self.load_limit_label)
        load_form.addRow("Movement:", self.load_state_combo)
        load_form.addRow("Commodity:", self.commodity_edit)
        load_form.addRow("Cargo Weight (lb):", self.cargo_weight_edit)
        load_form.addRow("Current Gross Weight:", self.gross_weight_label)
        load_form.addRow("Current Tonnage:", self.tonnage_label)
        layout.addWidget(load_group)

        compatibility_group = QGroupBox("Destination Compatibility")
        compatibility_form = QFormLayout(compatibility_group)
        self.allowed_car_type_label = QLabel("—")
        self.compatibility_label = QLabel("Select a car and destination.")
        self.compatibility_label.setWordWrap(True)
        compatibility_form.addRow(
            "Allowed Car Type:", self.allowed_car_type_label
        )
        compatibility_form.addRow("Compatibility:", self.compatibility_label)
        layout.addWidget(compatibility_group)

        notes_form = QFormLayout()
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Optional operational notes...")
        self.notes_edit.setMaximumHeight(90)
        notes_form.addRow("Notes:", self.notes_edit)
        layout.addLayout(notes_form)

        info_label = QLabel(
            "Yard, staging, and interchange endpoints require a Location and "
            "Track. Industry endpoints also require a Spot."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        car_image_group = QGroupBox("Car Picture")
        car_image_layout = QVBoxLayout(car_image_group)
        car_image_layout.addWidget(
            self.car_image_label,
            alignment=Qt.AlignCenter,
        )
        layout.addWidget(car_image_group)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.car_combo.currentIndexChanged.connect(self.car_changed)
        self.origin_location_combo.currentIndexChanged.connect(
            self.load_origin_tracks
        )
        self.origin_track_combo.currentIndexChanged.connect(
            self.load_origin_spots
        )
        self.destination_location_combo.currentIndexChanged.connect(
            self.load_destination_tracks
        )
        self.destination_track_combo.currentIndexChanged.connect(
            self.load_destination_spots
        )
        self.destination_spot_combo.currentIndexChanged.connect(
            self.update_compatibility
        )
        self.load_state_combo.currentIndexChanged.connect(
            self.update_weight_summary
        )
        self.cargo_weight_edit.textChanged.connect(
            self.update_weight_summary
        )

        self.load_locations()
        self.load_cars()
        self.load_operations_sessions()

        if self.waybill is not None:
            self.load_existing_waybill()
        else:
            self.car_changed()

    def load_locations(self):
        self.locations = [
            location
            for location in LocationService.get_all()
            if location.active and any(track.active for track in location.tracks)
        ]

        for combo in (
            self.origin_location_combo,
            self.destination_location_combo,
        ):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Select a location", None)
            for location in self.locations:
                combo.addItem(
                    f"{location.name} — {location.location_type.title()}",
                    location.id,
                )
            combo.blockSignals(False)

        self.load_origin_tracks()
        self.load_destination_tracks()

    def _location(self, location_id):
        return next(
            (location for location in self.locations if location.id == location_id),
            None,
        )

    def _load_tracks(self, location_combo, track_combo, spot_loader):
        track_combo.blockSignals(True)
        track_combo.clear()
        location = self._location(location_combo.currentData())

        if location is not None:
            for track in location.tracks:
                if track.active:
                    track_combo.addItem(
                        (
                            f"{track.name} — {track.track_type.title()}"
                            f" / {track.traffic_use.title()}"
                        ),
                        track.id,
                    )

        track_combo.blockSignals(False)
        spot_loader()

    def load_origin_tracks(self):
        self._load_tracks(
            self.origin_location_combo,
            self.origin_track_combo,
            self.load_origin_spots,
        )

    def load_destination_tracks(self):
        self._load_tracks(
            self.destination_location_combo,
            self.destination_track_combo,
            self.load_destination_spots,
        )

    def _load_spots(self, track_combo, spot_combo, destination=False):
        spot_combo.blockSignals(True)
        spot_combo.clear()
        track_id = track_combo.currentData()

        with SessionLocal() as session:
            industry_track = None
            if track_id is not None:
                industry_track = session.execute(
                    select(IndustryTrack).where(
                        IndustryTrack.operating_track_id == track_id
                    )
                ).scalars().first()

            if industry_track is None:
                spot_combo.addItem("Not required", None)
                spot_combo.setEnabled(False)
            else:
                spots = session.execute(
                    select(Spot)
                    .where(Spot.track_id == industry_track.id)
                    .order_by(Spot.spot_number)
                ).scalars().all()
                for spot in spots:
                    text = f"Spot {spot.spot_number}"
                    if spot.name:
                        text += f" - {spot.name}"
                    spot_combo.addItem(text, spot.id)
                spot_combo.setEnabled(True)

        spot_combo.blockSignals(False)
        if destination:
            self.update_compatibility()

    def load_origin_spots(self):
        self._load_spots(
            self.origin_track_combo,
            self.origin_spot_combo,
        )

    def load_destination_spots(self):
        self._load_spots(
            self.destination_track_combo,
            self.destination_spot_combo,
            destination=True,
        )

    def load_cars(self):
        self.car_combo.blockSignals(True)
        self.car_combo.clear()

        with SessionLocal() as session:
            current_car_id = (
                self.waybill.car_id
                if self.waybill is not None
                else None
            )

            unfinished_waybill_filters = (
                Waybill.car_id == Car.id,
                Waybill.status.in_(["ACTIVE", "IN_PROGRESS"]),
            )

            if self.waybill is not None:
                unfinished_waybill_filters += (
                    Waybill.id != self.waybill.id,
                )

            has_unfinished_waybill = (
                select(Waybill.id)
                .where(*unfinished_waybill_filters)
                .exists()
            )

            cars = session.execute(
                select(Car)
                .where(~has_unfinished_waybill)
                .order_by(Car.reporting_mark, Car.number)
            ).scalars().all()

            car_ids = {
                car.id
                for car in cars
            }

            if (
                current_car_id is not None
                and current_car_id not in car_ids
            ):
                current_car = session.get(
                    Car,
                    current_car_id,
                )

                if current_car is not None:
                    cars.append(current_car)
                    cars.sort(
                        key=lambda car: (
                            (car.reporting_mark or "").casefold(),
                            (car.number or "").casefold(),
                        )
                    )

            for car in cars:
                text = f"{car.reporting_mark} {car.number}"
                if car.car_type:
                    text += f" - {car.car_type}"

                self.car_combo.addItem(
                    text,
                    car.id,
                )

            if not cars:
                self.car_combo.addItem(
                    "No unassigned cars available",
                    None,
                )

        self.car_combo.blockSignals(False)

    def load_operations_sessions(self):
        self.operations_session_combo.clear()
        self.operations_session_combo.addItem(
            "No Operations Session",
            None,
        )

        with SessionLocal() as session:
            sessions = session.execute(
                select(OperationsSession)
                .where(
                    OperationsSession.status.in_(
                        ["PLANNED", "ACTIVE"]
                    )
                )
                .order_by(
                    OperationsSession.session_date.desc(),
                    OperationsSession.name,
                )
            ).scalars().all()

            for operations_session in sessions:
                date_text = (
                    operations_session.session_date.strftime("%Y-%m-%d")
                    if operations_session.session_date is not None
                    else ""
                )

                text = operations_session.name

                if date_text:
                    text += f" ({date_text})"

                self.operations_session_combo.addItem(
                    text,
                    operations_session.id,
                )

    def _select_endpoint(
        self,
        location_combo,
        track_combo,
        spot_combo,
        location_id,
        track_id,
        spot_id,
        track_loader,
        spot_loader,
    ):
        location_index = location_combo.findData(
            location_id
        )

        if location_index >= 0:
            location_combo.setCurrentIndex(
                location_index
            )

        track_loader()

        track_index = track_combo.findData(
            track_id
        )

        if track_index >= 0:
            track_combo.setCurrentIndex(
                track_index
            )

        spot_loader()

        spot_index = spot_combo.findData(
            spot_id
        )

        if spot_index >= 0:
            spot_combo.setCurrentIndex(
                spot_index
            )

    def car_changed(self):
        car_id = self.car_combo.currentData()

        with SessionLocal() as session:
            car = (
                session.get(Car, car_id)
                if car_id is not None
                else None
            )

            self.car_type_label.setText(
                car.car_type
                if car is not None and car.car_type
                else "Not specified"
            )

            self.empty_weight_label.setText(
                f"{car.empty_weight_lbs:,} lb"
                if (
                    car is not None
                    and car.empty_weight_lbs is not None
                )
                else "Not entered"
            )

            self.load_limit_label.setText(
                f"{car.load_limit_lbs:,} lb"
                if (
                    car is not None
                    and car.load_limit_lbs is not None
                )
                else "Not entered"
            )

            self.update_car_image(
                car
            )

            if (
                car is not None
                and self.waybill is None
                and not self.loading_existing
                and car.operating_location_id is not None
            ):
                self._select_endpoint(
                    self.origin_location_combo,
                    self.origin_track_combo,
                    self.origin_spot_combo,
                    car.operating_location_id,
                    car.operating_track_id,
                    car.spot_id,
                    self.load_origin_tracks,
                    self.load_origin_spots,
                )

        self.update_compatibility()
        self.update_weight_summary()

    def update_weight_summary(self, *_args):
        """Show gross pounds and short tons for the selected movement."""

        load_state = self.load_state_combo.currentData()

        self.cargo_weight_edit.setEnabled(
            load_state == "LOADED"
        )

        car_id = self.car_combo.currentData()

        with SessionLocal() as session:
            car = (
                session.get(Car, car_id)
                if car_id is not None
                else None
            )

            if (
                car is None
                or car.empty_weight_lbs is None
            ):
                self.gross_weight_label.setText(
                    "Enter Empty Weight on the Car Roster"
                )
                self.tonnage_label.setText(
                    "Not calculated"
                )
                return

            if load_state == "EMPTY":
                gross_weight_lbs = (
                    car.empty_weight_lbs
                )

            elif load_state == "LOADED":
                cargo_text = (
                    self.cargo_weight_edit.text()
                    .strip()
                    .replace(",", "")
                )

                try:
                    cargo_weight_lbs = int(
                        cargo_text
                    )
                except ValueError:
                    self.gross_weight_label.setText(
                        "Enter cargo weight"
                    )
                    self.tonnage_label.setText(
                        "Not calculated"
                    )
                    return

                if cargo_weight_lbs <= 0:
                    self.gross_weight_label.setText(
                        "Enter cargo weight"
                    )
                    self.tonnage_label.setText(
                        "Not calculated"
                    )
                    return

                gross_weight_lbs = (
                    car.empty_weight_lbs
                    + cargo_weight_lbs
                )

            else:
                self.gross_weight_label.setText(
                    "Select Loaded or Empty"
                )
                self.tonnage_label.setText(
                    "Not calculated"
                )
                return

        self.gross_weight_label.setText(
            f"{gross_weight_lbs:,} lb"
        )

        self.tonnage_label.setText(
            f"{gross_weight_lbs / 2000.0:,.1f} short tons"
        )

    def update_car_image(self, car):
        """Show the selected car's Waybill image before the Waybill is saved."""

        self.car_image_label.clear()

        if car is None:
            self.car_image_label.setText(
                "Select a car to preview its picture."
            )
            self.car_image_label.setToolTip("")
            return

        image_path = WaybillFormRenderer.find_car_image_path(
            car.reporting_mark,
            car.number,
        )

        if image_path is None:
            self.car_image_label.setText(
                "No picture available"
            )
            self.car_image_label.setToolTip("")
            return

        pixmap = QPixmap(
            str(image_path)
        )

        if pixmap.isNull():
            self.car_image_label.setText(
                "Picture could not be loaded"
            )
            self.car_image_label.setToolTip(
                str(image_path)
            )
            return

        self.car_image_label.setPixmap(
            pixmap.scaled(
                self.car_image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

        self.car_image_label.setToolTip(
            str(image_path)
        )

    def update_compatibility(self):
        spot_id = (
            self.destination_spot_combo.currentData()
        )

        car_id = (
            self.car_combo.currentData()
        )

        if not self.destination_spot_combo.isEnabled():
            self.allowed_car_type_label.setText(
                "Not applicable"
            )
            self.compatibility_label.setText(
                "Compatible — this destination is a general track."
            )
            return

        if car_id is None or spot_id is None:
            self.allowed_car_type_label.setText(
                "—"
            )
            self.compatibility_label.setText(
                "Select a car and destination spot."
            )
            return

        with SessionLocal() as session:
            car = session.get(
                Car,
                car_id,
            )

            spot = session.get(
                Spot,
                spot_id,
            )

            if car is None or spot is None:
                self.allowed_car_type_label.setText(
                    "—"
                )
                self.compatibility_label.setText(
                    "Selection could not be found."
                )
                return

            allowed = (
                spot.allowed_car_type
                or ""
            )

            self.allowed_car_type_label.setText(
                allowed or "Any"
            )

            if not allowed:
                message = (
                    "Compatible — this spot accepts any car type."
                )
            elif not car.car_type:
                message = (
                    "Check required — the car has no car type."
                )
            elif (
                car.car_type.strip().casefold()
                == allowed.strip().casefold()
            ):
                message = "Compatible"
            else:
                message = (
                    f"Not compatible — {car.car_type} "
                    f"does not match {allowed}."
                )

            self.compatibility_label.setText(
                message
            )

    def load_existing_waybill(self):
        self.loading_existing = True

        try:
            car_index = self.car_combo.findData(
                self.waybill.car_id
            )

            if car_index >= 0:
                self.car_combo.setCurrentIndex(
                    car_index
                )

            session_index = (
                self.operations_session_combo.findData(
                    self.waybill.operations_session_id
                )
            )

            self.operations_session_combo.setCurrentIndex(
                session_index
                if session_index >= 0
                else 0
            )

            origin_location_id = getattr(
                self.waybill,
                "origin_location_id",
                None,
            )

            origin_track_id = getattr(
                self.waybill,
                "origin_location_track_id",
                None,
            )

            destination_location_id = getattr(
                self.waybill,
                "destination_location_id",
                None,
            )

            destination_track_id = getattr(
                self.waybill,
                "destination_location_track_id",
                None,
            )

            if (
                origin_location_id is None
                and self.waybill.origin_industry
            ):
                origin_location_id = (
                    self.waybill.origin_industry.operating_location_id
                )

            if (
                origin_track_id is None
                and self.waybill.origin_track
            ):
                origin_track_id = (
                    self.waybill.origin_track.operating_track_id
                )

            if (
                destination_location_id is None
                and self.waybill.destination_industry
            ):
                destination_location_id = (
                    self.waybill.destination_industry.operating_location_id
                )

            if (
                destination_track_id is None
                and self.waybill.destination_track
            ):
                destination_track_id = (
                    self.waybill.destination_track.operating_track_id
                )

            self._select_endpoint(
                self.origin_location_combo,
                self.origin_track_combo,
                self.origin_spot_combo,
                origin_location_id,
                origin_track_id,
                self.waybill.origin_spot_id,
                self.load_origin_tracks,
                self.load_origin_spots,
            )

            self._select_endpoint(
                self.destination_location_combo,
                self.destination_track_combo,
                self.destination_spot_combo,
                destination_location_id,
                destination_track_id,
                self.waybill.destination_spot_id,
                self.load_destination_tracks,
                self.load_destination_spots,
            )

            self.notes_edit.setPlainText(
                self.waybill.notes or ""
            )

            load_state_index = (
                self.load_state_combo.findData(
                    getattr(
                        self.waybill,
                        "load_state",
                        None,
                    )
                )
            )

            self.load_state_combo.setCurrentIndex(
                load_state_index
                if load_state_index >= 0
                else 0
            )

            self.commodity_edit.setText(
                getattr(
                    self.waybill,
                    "commodity",
                    None,
                )
                or ""
            )

            cargo_weight_lbs = getattr(
                self.waybill,
                "cargo_weight_lbs",
                None,
            )

            self.cargo_weight_edit.setText(
                str(cargo_weight_lbs)
                if cargo_weight_lbs not in (None, 0)
                else ""
            )

        finally:
            self.loading_existing = False
            self.car_changed()

    def save(self):
        car_id = (
            self.car_combo.currentData()
        )

        origin_location_id = (
            self.origin_location_combo.currentData()
        )

        origin_track_id = (
            self.origin_track_combo.currentData()
        )

        destination_location_id = (
            self.destination_location_combo.currentData()
        )

        destination_track_id = (
            self.destination_track_combo.currentData()
        )

        if car_id is None:
            QMessageBox.warning(
                self,
                "Waybill",
                "Please select a car.",
            )
            return

        if (
            origin_location_id is None
            or origin_track_id is None
        ):
            QMessageBox.warning(
                self,
                "Waybill",
                "Please select an origin location and track.",
            )
            return

        if (
            destination_location_id is None
            or destination_track_id is None
        ):
            QMessageBox.warning(
                self,
                "Waybill",
                "Please select a destination location and track.",
            )
            return

        origin_spot_id = (
            self.origin_spot_combo.currentData()
        )

        destination_spot_id = (
            self.destination_spot_combo.currentData()
        )

        if (
            self.origin_spot_combo.isEnabled()
            and origin_spot_id is None
        ):
            QMessageBox.warning(
                self,
                "Waybill",
                "Industry origins require an origin spot.",
            )
            return

        if (
            self.destination_spot_combo.isEnabled()
            and destination_spot_id is None
        ):
            QMessageBox.warning(
                self,
                "Waybill",
                "Industry destinations require a spot.",
            )
            return

        load_state = (
            self.load_state_combo.currentData()
        )

        cargo_weight_lbs = None

        if load_state == "LOADED":
            cargo_text = (
                self.cargo_weight_edit.text()
                .strip()
                .replace(",", "")
            )

            try:
                cargo_weight_lbs = int(
                    cargo_text
                )
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Waybill",
                    "Please enter a whole-number cargo weight in pounds.",
                )
                return

        elif load_state == "EMPTY":
            cargo_weight_lbs = 0

        elif self.waybill is None:
            QMessageBox.warning(
                self,
                "Waybill",
                "Please select whether the car is Loaded or Empty.",
            )
            return

        origin_location = self._location(
            origin_location_id
        )

        values = {
            "car_id": car_id,
            "operations_session_id": (
                self.operations_session_combo.currentData()
            ),
            "origin_location": origin_location.name,
            "destination_industry_id": None,
            "destination_track_id": None,
            "destination_spot_id": destination_spot_id,
            "notes": (
                self.notes_edit.toPlainText().strip()
                or None
            ),
            "origin_location_id": origin_location_id,
            "origin_location_track_id": origin_track_id,
            "origin_spot_id": origin_spot_id,
            "destination_location_id": destination_location_id,
            "destination_location_track_id": destination_track_id,
            "load_state": load_state,
            "commodity": (
                self.commodity_edit.text().strip()
                or None
            ),
            "cargo_weight_lbs": cargo_weight_lbs,
        }

        if self.waybill is None:
            success, result = WaybillService.create(
                **values
            )
            title = "Add Waybill"
        else:
            success, result = WaybillService.update(
                waybill_id=self.waybill.id,
                **values,
            )
            title = "Edit Waybill"

        if not success:
            QMessageBox.warning(
                self,
                title,
                str(result),
            )
            return

        self.accept()