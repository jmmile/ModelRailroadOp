from PySide6.QtCore import QEvent, Qt, QTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
)

from modelrailroadops.services.location_service import LocationService
from modelrailroadops.services.train_route_service import TrainRouteService


class RouteStopTimeEdit(QTimeEdit):
    """Start click-to-type edits at the beginning of the time value."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineEdit().installEventFilter(self)

    def eventFilter(self, watched, event):
        if (
            watched is self.lineEdit()
            and event.type() == QEvent.MouseButtonRelease
            and event.button() == Qt.LeftButton
        ):
            self.setCurrentSection(QTimeEdit.HourSection)
            self.lineEdit().setSelection(
                0,
                len(self.sectionText(QTimeEdit.HourSection)),
            )

        return super().eventFilter(watched, event)


class AddTrainRouteDialog(QDialog):
    """Add or edit an ordered Train route stop."""

    def __init__(self, train_id, parent=None, route=None):
        super().__init__(parent)

        self.train_id = train_id
        self.route = route
        self.locations = []

        self.setWindowTitle(
            "Edit Train Route Stop" if route else "Add Train Route Stop"
        )
        self.resize(520, 400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        #
        # Sequence
        #

        self.sequence_spin = QSpinBox()
        self.sequence_spin.setRange(1, 9999)

        #
        # Location
        #

        self.location_combo = QComboBox()
        self.location_combo.setEditable(True)
        self.location_combo.setInsertPolicy(QComboBox.NoInsert)
        self.location_combo.setMinimumWidth(320)
        self.location_combo.lineEdit().setPlaceholderText(
            "Select a location or type a temporary location"
        )

        #
        # Track
        #

        self.track_combo = QComboBox()
        self.track_combo.setMinimumWidth(320)

        #
        # Industry
        #

        self.industry_label = QLabel("None")

        #
        # Scheduled arrival
        #

        arrival_layout = QHBoxLayout()

        self.arrival_checkbox = QCheckBox(
            "Scheduled"
        )

        self.arrival_time_edit = RouteStopTimeEdit()

        self.arrival_time_edit.setDisplayFormat(
            "h:mm AP"
        )

        self.arrival_time_edit.setEnabled(
            False
        )

        arrival_layout.addWidget(
            self.arrival_checkbox
        )

        arrival_layout.addWidget(
            self.arrival_time_edit
        )

        #
        # Scheduled departure
        #

        departure_layout = QHBoxLayout()

        self.departure_checkbox = QCheckBox(
            "Scheduled"
        )

        self.departure_time_edit = RouteStopTimeEdit()

        self.departure_time_edit.setDisplayFormat(
            "h:mm AP"
        )

        self.departure_time_edit.setEnabled(
            False
        )

        departure_layout.addWidget(
            self.departure_checkbox
        )

        departure_layout.addWidget(
            self.departure_time_edit
        )

        #
        # Description
        #

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText(
            "Optional description"
        )

        #
        # Form rows
        #

        form.addRow(
            "Sequence:",
            self.sequence_spin,
        )

        form.addRow(
            "Location:",
            self.location_combo,
        )

        form.addRow(
            "Track:",
            self.track_combo,
        )

        form.addRow(
            "Industry:",
            self.industry_label,
        )

        form.addRow(
            "Arrival:",
            arrival_layout,
        )

        form.addRow(
            "Departure:",
            departure_layout,
        )

        form.addRow(
            "Description:",
            self.description_edit,
        )

        layout.addLayout(
            form
        )

        #
        # Dialog buttons
        #

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            self.save
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(
            buttons
        )

        #
        # Signals
        #

        self.arrival_checkbox.toggled.connect(
            self.arrival_time_edit.setEnabled
        )

        self.departure_checkbox.toggled.connect(
            self.departure_time_edit.setEnabled
        )

        self.load_locations()

        self.location_combo.currentTextChanged.connect(
            self.location_changed
        )

        if route is not None:

            self.load_route()

        else:

            self.sequence_spin.setValue(
                TrainRouteService.get_next_sequence(
                    train_id
                )
            )

            if self.location_combo.count():

                self.location_combo.setCurrentIndex(
                    0
                )

            self.location_changed()

    def load_locations(self):

        self.location_combo.clear()

        self.locations = list(
            LocationService.get_all()
        )

        current_location_id = (
            self.route.location_id
            if self.route
            else None
        )

        for location in self.locations:

            if (
                location.active
                or location.id == current_location_id
            ):

                self.location_combo.addItem(
                    location.name,
                    location.id,
                )

    def get_selected_location(self):

        location_id = (
            self.location_combo.currentData()
        )

        return next(
            (
                location
                for location in self.locations
                if location.id == location_id
            ),
            None,
        )

    def location_changed(
        self,
        text=None,
    ):

        location = (
            self.get_selected_location()
        )

        current_track_id = (
            self.route.location_track_id
            if self.route
            else None
        )

        self.track_combo.clear()

        self.track_combo.addItem(
            "No specific track",
            None,
        )

        if location is None:

            self.track_combo.setEnabled(
                False
            )

            self.industry_label.setText(
                "None"
            )

            return

        self.track_combo.setEnabled(
            True
        )

        industry_names = [
            industry.name
            for industry in location.industries
        ]

        self.industry_label.setText(
            ", ".join(industry_names)
            if industry_names
            else "None"
        )

        for track in location.tracks:

            if (
                track.active
                or track.id == current_track_id
            ):

                label = (
                    f"{track.name} — "
                    f"{track.track_type.title()}"
                    f" / {track.traffic_use.title()}"
                )

                self.track_combo.addItem(
                    label,
                    track.id,
                )

        if current_track_id is not None:

            index = (
                self.track_combo.findData(
                    current_track_id
                )
            )

            if index >= 0:

                self.track_combo.setCurrentIndex(
                    index
                )

    def load_route(self):

        self.sequence_spin.setValue(
            int(
                self.route.sequence
            )
        )

        self.description_edit.setText(
            self.route.description
            or ""
        )

        if self.route.arrival_time is not None:

            arrival = (
                self.route.arrival_time
            )

            self.arrival_time_edit.setTime(
                QTime(
                    arrival.hour,
                    arrival.minute,
                    arrival.second,
                )
            )

            self.arrival_checkbox.setChecked(
                True
            )

        if self.route.departure_time is not None:

            departure = (
                self.route.departure_time
            )

            self.departure_time_edit.setTime(
                QTime(
                    departure.hour,
                    departure.minute,
                    departure.second,
                )
            )

            self.departure_checkbox.setChecked(
                True
            )

        index = (
            self.location_combo.findData(
                self.route.location_id
            )
        )

        if index >= 0:

            self.location_combo.setCurrentIndex(
                index
            )

        else:

            self.location_combo.setCurrentIndex(
                -1
            )

            self.location_combo.setEditText(
                self.route.location
                or ""
            )

        self.location_changed()

    def save(self):

        location = (
            self.location_combo.currentText()
            .strip()
        )

        if not location:

            QMessageBox.warning(
                self,
                "Train Route",
                "Route location is required.",
            )

            self.location_combo.setFocus()

            return

        arrival_time = (
            self.arrival_time_edit.time().toPython()
            if self.arrival_checkbox.isChecked()
            else None
        )

        departure_time = (
            self.departure_time_edit.time().toPython()
            if self.departure_checkbox.isChecked()
            else None
        )

        arguments = {
            "location": location,
            "location_id": self.location_combo.currentData(),
            "location_track_id": self.track_combo.currentData(),
            "sequence": self.sequence_spin.value(),
            "arrival_time": arrival_time,
            "departure_time": departure_time,
            "description": self.description_edit.text().strip(),
        }

        if self.route is None:

            success, result = (
                TrainRouteService.create(
                    train_id=self.train_id,
                    **arguments,
                )
            )

        else:

            success, result = (
                TrainRouteService.update(
                    route_id=self.route.id,
                    **arguments,
                )
            )

        if not success:

            QMessageBox.warning(
                self,
                "Train Route",
                str(result),
            )

            return

        self.accept()
