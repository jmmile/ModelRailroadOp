from PySide6.QtCore import QTime

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

from modelrailroadops.services.train_service import (
    TrainService,
)
from modelrailroadops.services.location_service import LocationService
from modelrailroadops.services.train_route_service import TrainRouteService
from modelrailroadops.models.train import Train


class AddTrainDialog(QDialog):
    """
    Dialog used to add or edit a Train.

    When an existing Train is supplied, the dialog
    loads its current values and updates that Train
    when saved.
    """

    def __init__(
        self,
        parent=None,
        train=None,
    ):

        super().__init__(
            parent
        )

        self.train = train
        self.locations = []

        if self.train is None:

            self.setWindowTitle(
                "Add Train"
            )

        else:

            self.setWindowTitle(
                "Edit Train"
            )

        self.resize(
            520,
            500,
        )

        #
        # Main layout
        #

        layout = QVBoxLayout(
            self
        )

        #
        # Form layout
        #

        form_layout = QFormLayout()

        #
        # Train Number
        #

        self.number_edit = QLineEdit()

        self.number_edit.setPlaceholderText(
            "Example: 101"
        )

        form_layout.addRow(
            "Train Number:",
            self.number_edit,
        )

        #
        # Train Name
        #

        self.name_edit = QLineEdit()

        self.name_edit.setPlaceholderText(
            "Example: Portland Local"
        )

        form_layout.addRow(
            "Train Name:",
            self.name_edit,
        )

        #
        # Train type
        #

        self.train_type_edit = QComboBox()
        self.train_type_edit.setEditable(True)
        self.train_type_edit.setInsertPolicy(QComboBox.NoInsert)

        for train_type, symbol_prefix in Train.TRAIN_TYPE_CHOICES:
            display_text = train_type
            if symbol_prefix:
                display_text += f" ({symbol_prefix})"
            self.train_type_edit.addItem(display_text, train_type)

        self.train_type_edit.setCurrentIndex(-1)
        self.train_type_edit.lineEdit().setPlaceholderText(
            "Select or enter a train type"
        )

        form_layout.addRow(
            "Train Type:",
            self.train_type_edit,
        )

        #
        # Calculated train symbol
        #

        self.symbol_label = QLabel("—")

        form_layout.addRow(
            "Train Symbol:",
            self.symbol_label,
        )

        #
        # Description
        #

        self.description_edit = QLineEdit()

        self.description_edit.setPlaceholderText(
            "Optional description"
        )

        form_layout.addRow(
            "Description:",
            self.description_edit,
        )

        #
        # Origin location and track
        #

        self.origin_location_combo = QComboBox()

        form_layout.addRow(
            "Origin Location:",
            self.origin_location_combo,
        )

        self.origin_track_combo = QComboBox()

        form_layout.addRow(
            "Origin Track:",
            self.origin_track_combo,
        )

        #
        # Destination location and track
        #

        self.destination_location_combo = QComboBox()

        form_layout.addRow(
            "Destination Location:",
            self.destination_location_combo,
        )

        self.destination_track_combo = QComboBox()

        for endpoint_combo in (
            self.origin_location_combo,
            self.origin_track_combo,
            self.destination_location_combo,
            self.destination_track_combo,
        ):
            endpoint_combo.setSizeAdjustPolicy(
                QComboBox.AdjustToMinimumContentsLengthWithIcon
            )
            endpoint_combo.setMinimumContentsLength(20)

        form_layout.addRow(
            "Destination Track:",
            self.destination_track_combo,
        )

        #
        # Direction
        #

        self.direction_edit = QLineEdit()

        self.direction_edit.setPlaceholderText(
            "Example: South"
        )

        form_layout.addRow(
            "Direction:",
            self.direction_edit,
        )

        #
        # Priority
        #

        self.priority_edit = QSpinBox()

        self.priority_edit.setRange(
            0,
            999,
        )

        self.priority_edit.setSpecialValueText(
            "Not set"
        )

        form_layout.addRow(
            "Priority:",
            self.priority_edit,
        )

        #
        # Operating days
        #

        self.operating_days_edit = QLineEdit()

        self.operating_days_edit.setPlaceholderText(
            "Example: MON,TUE,WED,THU,FRI or DAILY"
        )

        form_layout.addRow(
            "Operating Days:",
            self.operating_days_edit,
        )

        #
        # Scheduled departure
        #

        departure_layout = QHBoxLayout()

        self.departure_checkbox = QCheckBox(
            "Scheduled"
        )

        self.departure_time_edit = QTimeEdit()

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

        form_layout.addRow(
            "Departure:",
            departure_layout,
        )

        #
        # Scheduled arrival
        #

        arrival_layout = QHBoxLayout()

        self.arrival_checkbox = QCheckBox(
            "Scheduled"
        )

        self.arrival_time_edit = QTimeEdit()

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

        form_layout.addRow(
            "Arrival:",
            arrival_layout,
        )

        #
        # Active
        #

        self.active_checkbox = QCheckBox(
            "Train is active"
        )

        self.active_checkbox.setChecked(
            True
        )

        form_layout.addRow(
            "Status:",
            self.active_checkbox,
        )

        layout.addLayout(
            form_layout
        )

        #
        # Dialog buttons
        #

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        layout.addWidget(
            self.button_box
        )

        #
        # Signals
        #

        self.button_box.accepted.connect(
            self.save
        )

        self.button_box.rejected.connect(
            self.reject
        )

        self.departure_checkbox.toggled.connect(
            self.departure_time_edit.setEnabled
        )

        self.arrival_checkbox.toggled.connect(
            self.arrival_time_edit.setEnabled
        )

        self.number_edit.textChanged.connect(
            self.update_train_symbol
        )

        self.train_type_edit.currentTextChanged.connect(
            self.update_train_symbol
        )

        self.origin_location_combo.currentIndexChanged.connect(
            self.load_origin_tracks
        )

        self.destination_location_combo.currentIndexChanged.connect(
            self.load_destination_tracks
        )

        self.load_locations()

        #
        # Load existing Train
        #

        if self.train is not None:

            self.load_train()

        self.update_train_symbol()

    def current_train_type(self):
        selected_type_index = self.train_type_edit.currentIndex()
        selected_type_text = self.train_type_edit.currentText().strip()

        if (
            selected_type_index >= 0
            and selected_type_text
            == self.train_type_edit.itemText(selected_type_index)
        ):
            return self.train_type_edit.currentData() or ""

        return selected_type_text

    def update_train_symbol(self):
        symbol = Train.build_symbol(
            self.number_edit.text(),
            self.current_train_type(),
        )
        self.symbol_label.setText(symbol or "—")

    def load_locations(self):
        """Load operational locations that have at least one active track."""

        self.locations = [
            location
            for location in LocationService.get_all()
            if location.active
            and any(track.active for track in location.tracks)
        ]

        endpoint_combos = (
            (
                self.origin_location_combo,
                {"OUTBOUND", "BOTH"},
            ),
            (
                self.destination_location_combo,
                {"INBOUND", "BOTH"},
            ),
        )

        for combo, allowed_traffic_uses in endpoint_combos:
            combo.clear()
            combo.addItem("Select a location", None)

            for location in self.locations:
                if not any(
                    track.active
                    and track.traffic_use in allowed_traffic_uses
                    for track in location.tracks
                ):
                    continue

                location_type = location.location_type.replace("_", " ").title()
                combo.addItem(
                    f"{location.name} ({location_type})",
                    location.id,
                )

        self.load_origin_tracks()
        self.load_destination_tracks()

    def _load_tracks(
        self,
        location_combo,
        track_combo,
        allowed_traffic_uses,
        prompt,
    ):
        """Load the active tracks belonging to the selected location."""

        track_combo.clear()
        track_combo.addItem(prompt, None)

        location_id = location_combo.currentData()
        location = next(
            (
                item
                for item in self.locations
                if item.id == location_id
            ),
            None,
        )

        if location is None:
            return

        for track in location.tracks:
            if (
                not track.active
                or track.traffic_use not in allowed_traffic_uses
            ):
                continue

            track_type = track.track_type.replace("_", " ").title()
            traffic_use = track.traffic_use.replace("_", " ").title()
            track_combo.addItem(
                f"{track.name} ({track_type}, {traffic_use})",
                track.id,
            )

    def load_origin_tracks(self, *_):
        self._load_tracks(
            self.origin_location_combo,
            self.origin_track_combo,
            {"OUTBOUND", "BOTH"},
            "Select an outbound track",
        )

    def load_destination_tracks(self, *_):
        self._load_tracks(
            self.destination_location_combo,
            self.destination_track_combo,
            {"INBOUND", "BOTH"},
            "Select an inbound track",
        )

    def _select_endpoint(
        self,
        location_combo,
        track_combo,
        location_id,
        track_id,
        track_loader,
    ):
        location_index = location_combo.findData(location_id)

        if location_index < 0:
            return

        location_combo.setCurrentIndex(location_index)
        track_loader()

        track_index = track_combo.findData(track_id)
        if track_index >= 0:
            track_combo.setCurrentIndex(track_index)

    def load_train_endpoints(self):
        """Load endpoints from the route, falling back to legacy names."""

        routes = TrainRouteService.get_by_train(self.train.id)

        if routes:
            origin_route = routes[0]
            destination_route = routes[-1]

            def route_location_id(route):
                if route.location_id is not None:
                    return route.location_id

                location = next(
                    (
                        item
                        for item in self.locations
                        if item.name == route.location
                    ),
                    None,
                )
                return location.id if location is not None else None

            self._select_endpoint(
                self.origin_location_combo,
                self.origin_track_combo,
                route_location_id(origin_route),
                origin_route.location_track_id,
                self.load_origin_tracks,
            )
            self._select_endpoint(
                self.destination_location_combo,
                self.destination_track_combo,
                route_location_id(destination_route),
                destination_route.location_track_id,
                self.load_destination_tracks,
            )
            return

        endpoint_names = (
            (
                self.train.origin,
                self.origin_location_combo,
                self.origin_track_combo,
                self.load_origin_tracks,
            ),
            (
                self.train.destination,
                self.destination_location_combo,
                self.destination_track_combo,
                self.load_destination_tracks,
            ),
        )

        for name, location_combo, track_combo, track_loader in endpoint_names:
            location = next(
                (
                    item
                    for item in self.locations
                    if item.name == name
                ),
                None,
            )
            if location is not None:
                self._select_endpoint(
                    location_combo,
                    track_combo,
                    location.id,
                    None,
                    track_loader,
                )

    #
    # Load Train
    #

    def load_train(
        self,
    ):

        self.number_edit.setText(
            self.train.number
            or ""
        )

        self.name_edit.setText(
            self.train.name
            or ""
        )

        train_type = self.train.train_type or ""
        normalized_train_type = (
            "Extra Movement"
            if train_type.strip().casefold() == "extra"
            else train_type.strip()
        )
        train_type_index = self.train_type_edit.findData(
            normalized_train_type
        )

        if train_type_index < 0:
            for index in range(self.train_type_edit.count()):
                item_data = self.train_type_edit.itemData(index)
                if (
                    item_data
                    and item_data.casefold()
                    == normalized_train_type.casefold()
                ):
                    train_type_index = index
                    break

        if train_type_index >= 0:
            self.train_type_edit.setCurrentIndex(train_type_index)
        else:
            self.train_type_edit.setEditText(train_type)

        self.description_edit.setText(
            self.train.description
            or ""
        )

        self.load_train_endpoints()

        self.direction_edit.setText(
            self.train.direction
            or ""
        )

        self.priority_edit.setValue(
            self.train.priority
            or 0
        )

        self.operating_days_edit.setText(
            self.train.operating_days
            or ""
        )

        if self.train.scheduled_departure is not None:

            departure = self.train.scheduled_departure

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

        if self.train.scheduled_arrival is not None:

            arrival = self.train.scheduled_arrival

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

        self.active_checkbox.setChecked(
            bool(
                self.train.active
            )
        )

    #
    # Save
    #

    def save(
        self,
    ):

        number = (
            self.number_edit.text()
            .strip()
        )

        name = (
            self.name_edit.text()
            .strip()
        )

        train_type = self.current_train_type()

        description = (
            self.description_edit.text()
            .strip()
        )

        origin_location_id = self.origin_location_combo.currentData()
        origin_track_id = self.origin_track_combo.currentData()
        destination_location_id = self.destination_location_combo.currentData()
        destination_track_id = self.destination_track_combo.currentData()

        origin_location = next(
            (
                item
                for item in self.locations
                if item.id == origin_location_id
            ),
            None,
        )
        destination_location = next(
            (
                item
                for item in self.locations
                if item.id == destination_location_id
            ),
            None,
        )

        origin = origin_location.name if origin_location is not None else ""
        destination = (
            destination_location.name
            if destination_location is not None
            else ""
        )

        direction = (
            self.direction_edit.text()
            .strip()
        )

        priority = (
            self.priority_edit.value()
            or None
        )

        operating_days = (
            self.operating_days_edit.text()
            .strip()
        )

        scheduled_departure = (
            self.departure_time_edit.time().toPython()
            if self.departure_checkbox.isChecked()
            else None
        )

        scheduled_arrival = (
            self.arrival_time_edit.time().toPython()
            if self.arrival_checkbox.isChecked()
            else None
        )

        active = (
            self.active_checkbox.isChecked()
        )

        #
        # Validate required fields.
        #

        if not number:

            QMessageBox.warning(
                self,
                "Train",
                "Train number is required.",
            )

            self.number_edit.setFocus()

            return

        if not name:

            QMessageBox.warning(
                self,
                "Train",
                "Train name is required.",
            )

            self.name_edit.setFocus()

            return

        if origin_location_id is None:
            QMessageBox.warning(
                self,
                "Train",
                "Select an origin location.",
            )
            self.origin_location_combo.setFocus()
            return

        if origin_track_id is None:
            QMessageBox.warning(
                self,
                "Train",
                "Select an origin track.",
            )
            self.origin_track_combo.setFocus()
            return

        if destination_location_id is None:
            QMessageBox.warning(
                self,
                "Train",
                "Select a destination location.",
            )
            self.destination_location_combo.setFocus()
            return

        if destination_track_id is None:
            QMessageBox.warning(
                self,
                "Train",
                "Select a destination track.",
            )
            self.destination_track_combo.setFocus()
            return

        #
        # Create new Train
        #

        creating_train = self.train is None

        if creating_train:

            success, result = (
                TrainService.create(
                    name=name,
                    number=number,
                    description=description,
                    origin=origin,
                    destination=destination,
                    direction=direction,
                    active=active,
                    train_type=train_type,
                    priority=priority,
                    operating_days=operating_days,
                    scheduled_departure=scheduled_departure,
                    scheduled_arrival=scheduled_arrival,
                )
            )

        #
        # Update existing Train
        #

        else:

            success, result = (
                TrainService.update(
                    train_id=self.train.id,
                    name=name,
                    number=number,
                    description=description,
                    origin=origin,
                    destination=destination,
                    direction=direction,
                    active=active,
                    train_type=train_type,
                    priority=priority,
                    operating_days=operating_days,
                    scheduled_departure=scheduled_departure,
                    scheduled_arrival=scheduled_arrival,
                )
            )

        #
        # Handle failure
        #

        if not success:

            QMessageBox.warning(
                self,
                "Train",
                str(
                    result
                ),
            )

            return

        saved_train_id = result.id
        endpoints_success, endpoints_result = TrainRouteService.set_endpoints(
            train_id=saved_train_id,
            origin_location_id=origin_location_id,
            origin_track_id=origin_track_id,
            destination_location_id=destination_location_id,
            destination_track_id=destination_track_id,
        )

        if not endpoints_success:
            if creating_train:
                TrainService.delete(saved_train_id)
                message = str(endpoints_result)
            else:
                message = (
                    "The train details were saved, but its route endpoints "
                    f"could not be updated: {endpoints_result}"
                )

            QMessageBox.warning(
                self,
                "Train Route",
                message,
            )
            return

        #
        # Success
        #

        self.accept()
