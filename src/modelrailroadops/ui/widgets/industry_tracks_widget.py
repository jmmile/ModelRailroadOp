#```python
from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QMessageBox,
    QAbstractItemView,
    QHeaderView,
    QLabel,
)

from modelrailroadops.ui.models.industry_track_table_model import (
    IndustryTrackTableModel,
)

from modelrailroadops.ui.dialogs.add_industry_track_dialog import (
    AddIndustryTrackDialog,
)

from modelrailroadops.ui.dialogs.add_spot_dialog import (
    AddSpotDialog,
)

from modelrailroadops.services.industry_track_service import (
    IndustryTrackService,
)

from modelrailroadops.services.spot_service import (
    SpotService,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)


class IndustryTracksWidget(QWidget):
    """
    Displays and manages industry tracks and their spots.
    """

    SPOT_ID_ROLE = Qt.UserRole
    OCCUPIED_ROLE = Qt.UserRole + 1

    def __init__(self):

        super().__init__()

        #
        # Track model
        #

        self.model = IndustryTrackTableModel()

        #
        # Track table
        #

        self.table = QTableView()

        self.table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.table.setModel(
            self.model
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.table.horizontalHeader().setStretchLastSection(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        #
        # Spot section label
        #

        self.spot_label = QLabel(
            "Spots - Select a track"
        )

        #
        # Spot table
        #

        self.spot_table = QTableWidget()

        self.spot_table.setColumnCount(
            8
        )

        self.spot_table.setHorizontalHeaderLabels(
            [
                "Spot",
                "Name",
                "Description",
                "Max Length",
                "Allowed Car Type",
                "Allowed Owner",
                "Load / Empty",
                "Status",
            ]
        )

        self.spot_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.spot_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.spot_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.spot_table.setAlternatingRowColors(
            True
        )

        self.spot_table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.spot_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.spot_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.spot_table.verticalHeader().setVisible(
            False
        )

        #
        # Track buttons
        #

        self.add_button = QPushButton(
            "Add Track"
        )

        self.edit_button = QPushButton(
            "Edit Track"
        )

        #
        # Spot buttons
        #

        self.add_spot_button = QPushButton(
            "Add Spot"
        )

        self.edit_spot_button = QPushButton(
            "Edit Spot"
        )

        self.delete_spot_button = QPushButton(
            "Delete Spot"
        )

        #
        # Refresh
        #

        self.refresh_button = QPushButton(
            "Refresh"
        )

        #
        # Track button layout
        #

        track_button_layout = QHBoxLayout()

        track_button_layout.addWidget(
            self.add_button
        )

        track_button_layout.addWidget(
            self.edit_button
        )

        track_button_layout.addStretch()

        #
        # Spot button layout
        #

        spot_button_layout = QHBoxLayout()

        spot_button_layout.addWidget(
            self.add_spot_button
        )

        spot_button_layout.addWidget(
            self.edit_spot_button
        )

        spot_button_layout.addWidget(
            self.delete_spot_button
        )

        spot_button_layout.addStretch()

        spot_button_layout.addWidget(
            self.refresh_button
        )

        #
        # Main layout
        #

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            QLabel("Industry Tracks")
        )

        layout.addWidget(
            self.table
        )

        layout.addLayout(
            track_button_layout
        )

        layout.addWidget(
            self.spot_label
        )

        layout.addWidget(
            self.spot_table
        )

        layout.addLayout(
            spot_button_layout
        )

        self.setLayout(
            layout
        )

        #
        # Signals
        #

        self.add_button.clicked.connect(
            self.add_track
        )

        self.edit_button.clicked.connect(
            self.edit_track
        )

        self.add_spot_button.clicked.connect(
            self.add_spot
        )

        self.edit_spot_button.clicked.connect(
            self.edit_spot
        )

        self.delete_spot_button.clicked.connect(
            self.delete_spot
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.table.selectionModel().selectionChanged.connect(
            self.track_selection_changed
        )

        self.spot_table.itemSelectionChanged.connect(
            self.spot_selection_changed
        )

        #
        # Initial state
        #

        self.refresh()

    #
    # Refresh everything
    #

    def refresh(self):

        self.model.refresh()

        self.table.resizeColumnsToContents()

        self.load_spots()

        self.update_button_state()

    #
    # Get selected track
    #

    def get_selected_track(self):

        index = self.table.currentIndex()

        if not index.isValid():

            return None

        if index.row() >= len(
            self.model.tracks
        ):

            return None

        return self.model.tracks[
            index.row()
        ]

    #
    # Track selection changed
    #

    def track_selection_changed(
        self,
        selected,
        deselected,
    ):

        self.spot_table.clearSelection()

        self.load_spots()

        self.update_button_state()

    #
    # Check occupancy directly from
    # the Car table.
    #

    def is_spot_occupied(
        self,
        spot_id,
    ):

        with SessionLocal() as session:

            car = (
                session.query(Car)
                .filter(
                    Car.spot_id == spot_id
                )
                .first()
            )

            return car is not None

    #
    # Get car occupying a spot.
    #

    def get_car_for_spot(
        self,
        spot_id,
    ):

        with SessionLocal() as session:

            return (
                session.query(Car)
                .filter(
                    Car.spot_id == spot_id
                )
                .first()
            )

    #
    # Load spots
    #

    def load_spots(self):

        self.spot_table.setRowCount(
            0
        )

        track = self.get_selected_track()

        if track is None:

            self.spot_label.setText(
                "Spots - Select a track"
            )

            self.update_button_state()

            return

        self.spot_label.setText(
            f"Spots - {track.name}"
        )

        spots = SpotService.get_by_track(
            track.id
        )

        for spot in spots:

            row = self.spot_table.rowCount()

            self.spot_table.insertRow(
                row
            )

            #
            # Determine occupancy from
            # the database while loading.
            #

            occupied = self.is_spot_occupied(
                spot.id
            )

            #
            # Spot number
            #

            spot_item = QTableWidgetItem(
                str(spot.spot_number)
            )

            spot_item.setData(
                self.SPOT_ID_ROLE,
                spot.id
            )

            spot_item.setData(
                self.OCCUPIED_ROLE,
                occupied
            )

            self.spot_table.setItem(
                row,
                0,
                spot_item
            )

            #
            # Name
            #

            self.spot_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    spot.name or ""
                )
            )

            #
            # Description
            #

            self.spot_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    spot.description or ""
                )
            )

            #
            # Maximum length
            #

            max_length = (
                "No Limit"
                if spot.max_length is None
                else f"{spot.max_length} ft"
            )

            self.spot_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    max_length
                )
            )

            #
            # Allowed car type
            #

            self.spot_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    spot.allowed_car_type
                    or "Any"
                )
            )

            #
            # Allowed owner
            #

            self.spot_table.setItem(
                row,
                5,
                QTableWidgetItem(
                    spot.allowed_owner
                    or "Any"
                )
            )

            #
            # Loading restrictions
            #

            if spot.load_only:

                load_status = "Loaded Only"

            elif spot.empty_only:

                load_status = "Empty Only"

            else:

                load_status = "Loaded / Empty"

            self.spot_table.setItem(
                row,
                6,
                QTableWidgetItem(
                    load_status
                )
            )

            #
            # Occupancy
            #

            if occupied:

                car = self.get_car_for_spot(
                    spot.id
                )

                if car is not None:

                    car_text = (
                        f"{car.reporting_mark}"
                        f" {car.number}"
                    )

                    status = (
                        f"Occupied - {car_text}"
                    )

                else:

                    status = "Occupied"

            else:

                status = "Empty"

            self.spot_table.setItem(
                row,
                7,
                QTableWidgetItem(
                    status
                )
            )

        self.spot_table.resizeColumnsToContents()

        self.update_button_state()

    #
    # Get selected spot ID
    #

    def get_selected_spot_id(self):

        row = self.spot_table.currentRow()

        if row < 0:

            return None

        item = self.spot_table.item(
            row,
            0
        )

        if item is None:

            return None

        spot_id = item.data(
            self.SPOT_ID_ROLE
        )

        if spot_id is None:

            return None

        return int(
            spot_id
        )

    #
    # Get selected spot
    #

    def get_selected_spot(self):

        spot_id = self.get_selected_spot_id()

        if spot_id is None:

            return None

        track = self.get_selected_track()

        if track is None:

            return None

        spots = SpotService.get_by_track(
            track.id
        )

        for spot in spots:

            if spot.id == spot_id:

                return spot

        return None

    #
    # Spot selection changed
    #

    def spot_selection_changed(self):

        self.update_button_state()

    #
    # Update button state
    #

    def update_button_state(self):

        track = self.get_selected_track()

        track_selected = (
            track is not None
        )

        self.edit_button.setEnabled(
            track_selected
        )

        self.add_spot_button.setEnabled(
            track_selected
        )

        spot_id = self.get_selected_spot_id()

        spot_selected = (
            spot_id is not None
        )

        self.edit_spot_button.setEnabled(
            spot_selected
        )

        #
        # Delete is enabled ONLY when
        # a spot is selected AND the
        # database says the spot is empty.
        #

        if not spot_selected:

            self.delete_spot_button.setEnabled(
                False
            )

            return

        occupied = self.is_spot_occupied(
            spot_id
        )

        self.delete_spot_button.setEnabled(
            not occupied
        )

    #
    # Add track
    #

    def add_track(self):

        selected = self.table.currentIndex()

        if not selected.isValid():

            QMessageBox.warning(
                self,
                "No Industry Selected",
                "Select an industry before adding a track."
            )

            return

        industry = (
            self.model.tracks[
                selected.row()
            ].industry
        )

        dialog = AddIndustryTrackDialog(
            parent=self
        )

        if dialog.exec():

            name = (
                dialog.name.text()
                .strip()
            )

            if not name:

                QMessageBox.warning(
                    self,
                    "Missing Track Name",
                    "Please enter a track name."
                )

                return

            result = IndustryTrackService.add(
                industry_id=industry.id,
                name=name,
                spots=dialog.spots.value(),
            )

            if result:

                self.refresh()

            else:

                QMessageBox.warning(
                    self,
                    "Add Track Failed",
                    "The industry track could not be added."
                )

    #
    # Edit track
    #

    def edit_track(self):

        track = self.get_selected_track()

        if track is None:

            QMessageBox.warning(
                self,
                "No Track Selected",
                "Select a track to edit."
            )

            return

        dialog = AddIndustryTrackDialog(
            track=track,
            parent=self
        )

        if dialog.exec():

            result = IndustryTrackService.update(
                track.id,
                dialog.name.text().strip(),
                dialog.spots.value(),
            )

            if result:

                self.refresh()

            else:

                QMessageBox.warning(
                    self,
                    "Update Failed",
                    "Cannot reduce spots because some spots contain cars."
                )

    #
    # Add spot
    #

    def add_spot(self):

        track = self.get_selected_track()

        if track is None:

            QMessageBox.warning(
                self,
                "No Track Selected",
                "Select a track before adding a spot."
            )

            return

        dialog = AddSpotDialog(
            track=track,
            parent=self,
        )

        if dialog.exec():

            data = dialog.get_data()

            try:

                SpotService.add(
                    track_id=track.id,
                    spot_number=data["spot_number"],
                    name=data["name"],
                    description=data["description"],
                    max_length=data["max_length"],
                    allowed_car_type=data[
                        "allowed_car_type"
                    ],
                    allowed_owner=data[
                        "allowed_owner"
                    ],
                    hazardous_allowed=data[
                        "hazardous_allowed"
                    ],
                    load_only=data[
                        "load_only"
                    ],
                    empty_only=data[
                        "empty_only"
                    ],
                    notes=data["notes"],
                )

                self.load_spots()

            except Exception as ex:

                QMessageBox.warning(
                    self,
                    "Add Spot Failed",
                    str(ex)
                )

    #
    # Edit spot
    #

    def edit_spot(self):

        track = self.get_selected_track()

        if track is None:

            return

        spot = self.get_selected_spot()

        if spot is None:

            QMessageBox.warning(
                self,
                "No Spot Selected",
                "Select a spot to edit."
            )

            return

        dialog = AddSpotDialog(
            spot=spot,
            track=track,
            parent=self,
        )

        if dialog.exec():

            data = dialog.get_data()

            result = SpotService.update(
                spot_id=spot.id,
                name=data["name"],
                description=data["description"],
                max_length=data["max_length"],
                allowed_car_type=data[
                    "allowed_car_type"
                ],
                allowed_owner=data[
                    "allowed_owner"
                ],
                hazardous_allowed=data[
                    "hazardous_allowed"
                ],
                load_only=data[
                    "load_only"
                ],
                empty_only=data[
                    "empty_only"
                ],
                notes=data["notes"],
            )

            if result:

                self.load_spots()

            else:

                QMessageBox.warning(
                    self,
                    "Update Failed",
                    "The spot could not be updated."
                )

    #
    # Delete spot
    #

    def delete_spot(self):

        spot_id = self.get_selected_spot_id()

        if spot_id is None:

            QMessageBox.warning(
                self,
                "No Spot Selected",
                "Select a spot to delete."
            )

            return

        #
        # ALWAYS check the database immediately
        # before allowing deletion.
        #

        if self.is_spot_occupied(
            spot_id
        ):

            QMessageBox.warning(
                self,
                "Spot Occupied",
                "This spot contains a car and cannot be deleted."
            )

            self.update_button_state()

            return

        spot = self.get_selected_spot()

        if spot is None:

            QMessageBox.warning(
                self,
                "Spot Not Found",
                "The selected spot could not be found."
            )

            self.load_spots()

            return

        answer = QMessageBox.question(
            self,
            "Delete Spot",
            (
                f"Are you sure you want to delete "
                f"Spot {spot.spot_number}?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        #
        # Check one final time before deletion.
        #

        if self.is_spot_occupied(
            spot_id
        ):

            QMessageBox.warning(
                self,
                "Spot Occupied",
                "This spot now contains a car and cannot be deleted."
            )

            self.load_spots()

            return

        result = SpotService.delete(
            spot_id
        )

        if result:

            self.load_spots()

        else:

            QMessageBox.warning(
                self,
                "Delete Failed",
                "The spot could not be deleted."
            )

            self.load_spots()
#```
