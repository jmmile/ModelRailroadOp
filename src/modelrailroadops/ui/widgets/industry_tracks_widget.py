from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car

from modelrailroadops.services.industry_track_service import (
    IndustryTrackService,
)

from modelrailroadops.services.spot_service import (
    SpotService,
)

from modelrailroadops.ui.dialogs.add_industry_track_dialog import (
    AddIndustryTrackDialog,
)

from modelrailroadops.ui.dialogs.add_spot_dialog import (
    AddSpotDialog,
)

from modelrailroadops.ui.models.industry_track_table_model import (
    IndustryTrackTableModel,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)


class IndustryTracksWidget(QWidget):
    """
    Displays and manages industry tracks and their spots.

    Industries with zero tracks are displayed by the track model.
    Selecting an industry with no tracks allows the user to add
    its first track.

    Track deletion rules:

        - Tracks containing cars cannot be deleted.
        - Tracks with no cars can be deleted.
        - Tracks with empty spots can be deleted.
        - Tracks containing cars cannot be deleted.

    Spot deletion rules:

        - A spot containing a car cannot be deleted.
        - An empty spot can be deleted.
    """

    SPOT_ID_ROLE = Qt.ItemDataRole.UserRole
    OCCUPIED_ROLE = Qt.ItemDataRole.UserRole + 1

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
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSortingEnabled(
            True
        )

        self.table.horizontalHeader().setSortIndicatorShown(
            True
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
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
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.spot_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.spot_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.spot_table.setAlternatingRowColors(
            True
        )

        self.spot_table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.spot_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
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

        self.delete_track_button = QPushButton(
            "Delete Track"
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
        # Refresh button
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

        track_button_layout.addWidget(
            self.delete_track_button
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
            QLabel(
                "Industry Tracks"
            )
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

        #
        # Signals
        #

        self.add_button.clicked.connect(
            self.add_track
        )

        self.edit_button.clicked.connect(
            self.edit_track
        )

        self.delete_track_button.clicked.connect(
            self.delete_track
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

        self.update_button_state()

        self.refresh()

    # ------------------------------------------------------------------
    # Refresh whenever the tab becomes visible
    # ------------------------------------------------------------------

    def showEvent(
        self,
        event,
    ):

        self.refresh()

        super().showEvent(
            event
        )

    # ------------------------------------------------------------------
    # Refresh everything
    # ------------------------------------------------------------------

    def refresh(
        self,
        preserve_track_id=None,
        preserve_spot_id=None,
    ):

        #
        # Remember the current selection before rebuilding
        # the model.
        #

        if preserve_track_id is None:

            current_track = self.get_selected_track()

            if current_track is not None:

                preserve_track_id = current_track.id

        if preserve_spot_id is None:

            preserve_spot_id = (
                self.get_selected_spot_id()
            )

        #
        # Refresh the track model.
        #

        self.model.refresh()

        self.table.viewport().update()

        self.table.resizeColumnsToContents()

        #
        # Clear old selections before restoring the
        # appropriate selection.
        #

        self.table.clearSelection()

        self.spot_table.clearSelection()

        #
        # Restore the track selection when possible.
        #

        restored_track = False

        if preserve_track_id is not None:

            for row_number, row in enumerate(
                self.model.tracks
            ):

                track = row.get(
                    "track"
                )

                if (
                    track is not None
                    and track.id == preserve_track_id
                ):

                    index = self.model.index(
                        row_number,
                        0,
                    )

                    if index.isValid():

                        self.table.setCurrentIndex(
                            index
                        )

                        self.table.selectRow(
                            row_number
                        )

                        restored_track = True

                    break

        #
        # If no track was restored, load the empty state.
        #

        if restored_track:

            self.load_spots(
                preserve_spot_id=preserve_spot_id
            )

        else:

            self.load_spots()

        self.update_button_state()

    # ------------------------------------------------------------------
    # Get selected row
    # ------------------------------------------------------------------

    def get_selected_row(
        self,
    ):

        selection_model = (
            self.table.selectionModel()
        )

        if selection_model is None:

            return None

        selected_rows = (
            selection_model.selectedRows()
        )

        if not selected_rows:

            return None

        row_number = selected_rows[0].row()

        if row_number < 0:

            return None

        if row_number >= len(
            self.model.tracks
        ):

            return None

        return self.model.tracks[
            row_number
        ]

    # ------------------------------------------------------------------
    # Get selected industry
    # ------------------------------------------------------------------

    def get_selected_industry(
        self,
    ):

        row = self.get_selected_row()

        if row is None:

            return None

        return row.get(
            "industry"
        )

    # ------------------------------------------------------------------
    # Get selected track
    # ------------------------------------------------------------------

    def get_selected_track(
        self,
    ):

        row = self.get_selected_row()

        if row is None:

            return None

        return row.get(
            "track"
        )

    # ------------------------------------------------------------------
    # Track selection changed
    # ------------------------------------------------------------------

    def track_selection_changed(
        self,
        selected,
        deselected,
    ):

        self.spot_table.clearSelection()

        self.load_spots()

        self.update_button_state()

    # ------------------------------------------------------------------
    # Check whether a spot is occupied
    # ------------------------------------------------------------------

    def is_spot_occupied(
        self,
        spot_id,
    ):

        if spot_id is None:

            return False

        with SessionLocal() as session:

            car = (
                session.query(Car)
                .filter(
                    Car.spot_id == spot_id
                )
                .first()
            )

            return car is not None

    # ------------------------------------------------------------------
    # Get car occupying a spot
    # ------------------------------------------------------------------

    def get_car_for_spot(
        self,
        spot_id,
    ):

        if spot_id is None:

            return None

        with SessionLocal() as session:

            return (
                session.query(Car)
                .filter(
                    Car.spot_id == spot_id
                )
                .first()
            )

    # ------------------------------------------------------------------
    # Determine whether a track contains cars
    # ------------------------------------------------------------------

    def track_has_cars(
        self,
        track,
    ):

        if track is None:

            return False

        with SessionLocal() as session:

            car = (
                session.query(Car)
                .filter(
                    Car.track_id == track.id
                )
                .first()
            )

            return car is not None

    # ------------------------------------------------------------------
    # Load spots
    # ------------------------------------------------------------------

    def load_spots(
        self,
        preserve_spot_id=None,
    ):

        self.spot_table.setRowCount(
            0
        )

        industry = self.get_selected_industry()

        track = self.get_selected_track()

        #
        # No industry selected.
        #

        if industry is None:

            self.spot_label.setText(
                "Spots - Select an industry"
            )

            self.update_button_state()

            return

        #
        # Industry selected but no track.
        #

        if track is None:

            self.spot_label.setText(
                f"Spots - {industry.name} "
                "(No track selected)"
            )

            self.update_button_state()

            return

        #
        # Track selected.
        #

        self.spot_label.setText(
            f"Spots - {industry.name} / "
            f"{track.name}"
        )

        spots = SpotService.get_by_track(
            track.id
        )

        for spot in spots:

            row = (
                self.spot_table.rowCount()
            )

            self.spot_table.insertRow(
                row
            )

            occupied = (
                self.is_spot_occupied(
                    spot.id
                )
            )

            #
            # Spot number
            #

            spot_item = QTableWidgetItem(
                str(
                    spot.spot_number
                )
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
                    spot.allowed_car_type or "Any"
                )
            )

            #
            # Allowed owner
            #

            self.spot_table.setItem(
                row,
                5,
                QTableWidgetItem(
                    spot.allowed_owner or "Any"
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
            # Occupancy status
            #

            if occupied:

                car = self.get_car_for_spot(
                    spot.id
                )

                if car is not None:

                    car_text = (
                        f"{car.reporting_mark} "
                        f"{car.number}"
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

        #
        # Restore the previously selected spot.
        #

        if preserve_spot_id is not None:

            for row_number in range(
                self.spot_table.rowCount()
            ):

                item = (
                    self.spot_table.item(
                        row_number,
                        0,
                    )
                )

                if item is None:

                    continue

                spot_id = item.data(
                    self.SPOT_ID_ROLE
                )

                if (
                    spot_id is not None
                    and int(spot_id)
                    == int(preserve_spot_id)
                ):

                    self.spot_table.selectRow(
                        row_number
                    )

                    break

        self.update_button_state()

    # ------------------------------------------------------------------
    # Get selected spot ID
    # ------------------------------------------------------------------

    def get_selected_spot_id(
        self,
    ):

        selection_model = (
            self.spot_table.selectionModel()
        )

        if selection_model is None:

            return None

        selected_rows = (
            selection_model.selectedRows()
        )

        if not selected_rows:

            return None

        row = selected_rows[0].row()

        if row < 0:

            return None

        item = self.spot_table.item(
            row,
            0,
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

    # ------------------------------------------------------------------
    # Get selected spot
    # ------------------------------------------------------------------

    def get_selected_spot(
        self,
    ):

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

    # ------------------------------------------------------------------
    # Spot selection changed
    # ------------------------------------------------------------------

    def spot_selection_changed(
        self,
    ):

        self.update_button_state()

    # ------------------------------------------------------------------
    # Update button state
    # ------------------------------------------------------------------

    def update_button_state(
        self,
    ):

        industry = self.get_selected_industry()

        industry_selected = (
            industry is not None
        )

        #
        # Add Track
        #

        self.add_button.setEnabled(
            industry_selected
        )

        #
        # Selected track
        #

        track = self.get_selected_track()

        track_selected = (
            track is not None
        )

        #
        # Edit Track
        #

        self.edit_button.setEnabled(
            track_selected
        )

        #
        # Delete Track
        #

        if track_selected:

            self.delete_track_button.setEnabled(
                not self.track_has_cars(
                    track
                )
            )

        else:

            self.delete_track_button.setEnabled(
                False
            )

        #
        # Spot operations
        #

        self.add_spot_button.setEnabled(
            track_selected
        )

        spot_id = (
            self.get_selected_spot_id()
        )

        spot_selected = (
            spot_id is not None
            and track_selected
        )

        self.edit_spot_button.setEnabled(
            spot_selected
        )

        if not spot_selected:

            self.delete_spot_button.setEnabled(
                False
            )

            return

        occupied = (
            self.is_spot_occupied(
                spot_id
            )
        )

        self.delete_spot_button.setEnabled(
            not occupied
        )

    # ------------------------------------------------------------------
    # Add track
    # ------------------------------------------------------------------

    def add_track(
        self,
    ):

        industry = self.get_selected_industry()

        if industry is None:

            QMessageBox.warning(
                self,
                "No Industry Selected",
                "Select an industry before adding a track.",
            )

            return

        dialog = AddIndustryTrackDialog(
            parent=self
        )

        if (
            dialog.exec()
            != dialog.DialogCode.Accepted
        ):

            return

        name = (
            dialog.name.text()
            .strip()
        )

        if not name:

            QMessageBox.warning(
                self,
                "Missing Track Name",
                "Please enter a track name.",
            )

            return

        result = IndustryTrackService.add(
            industry_id=industry.id,
            name=name,
            spots=dialog.spots.value(),
        )

        if result:

            QMessageBox.information(
                self,
                "Track Added",
                f"Track '{name}' added successfully.",
            )

            self.refresh()

        else:

            QMessageBox.warning(
                self,
                "Add Track Failed",
                "The industry track could not be added.",
            )

    # ------------------------------------------------------------------
    # Edit track
    # ------------------------------------------------------------------

    def edit_track(
        self,
    ):

        track = self.get_selected_track()

        if track is None:

            QMessageBox.warning(
                self,
                "No Track Selected",
                "Select a track to edit.",
            )

            return

        dialog = AddIndustryTrackDialog(
            track=track,
            parent=self,
        )

        if (
            dialog.exec()
            != dialog.DialogCode.Accepted
        ):

            return

        name = (
            dialog.name.text()
            .strip()
        )

        if not name:

            QMessageBox.warning(
                self,
                "Missing Track Name",
                "Please enter a track name.",
            )

            return

        result = IndustryTrackService.update(
            track.id,
            name,
            dialog.spots.value(),
        )

        if result:

            QMessageBox.information(
                self,
                "Track Updated",
                f"Track '{name}' updated successfully.",
            )

            self.refresh(
                preserve_track_id=track.id
            )

        else:

            QMessageBox.warning(
                self,
                "Update Failed",
                (
                    "The track could not be updated. "
                    "If you reduced the number of spots, "
                    "make sure the spots being removed "
                    "do not contain cars."
                ),
            )

            self.refresh(
                preserve_track_id=track.id
            )

    # ------------------------------------------------------------------
    # Delete track
    # ------------------------------------------------------------------

    def delete_track(
        self,
    ):

        track = self.get_selected_track()

        if track is None:

            QMessageBox.warning(
                self,
                "No Track Selected",
                "Select a track to delete.",
            )

            return

        #
        # Final database occupancy check.
        #

        if self.track_has_cars(
            track
        ):

            QMessageBox.warning(
                self,
                "Track Occupied",
                (
                    "This track contains one or more cars "
                    "and cannot be deleted."
                ),
            )

            self.update_button_state()

            return

        track_id = track.id
        track_name = track.name

        answer = QMessageBox.question(
            self,
            "Delete Track",
            (
                f"Are you sure you want to delete "
                f"track '{track_name}'?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):

            return

        #
        # Final occupancy check immediately before deletion.
        #

        if self.track_has_cars(
            track
        ):

            QMessageBox.warning(
                self,
                "Track Occupied",
                (
                    "This track now contains one or more "
                    "cars and cannot be deleted."
                ),
            )

            self.update_button_state()

            return

        result = IndustryTrackService.delete(
            track_id
        )

        if result:

            QMessageBox.information(
                self,
                "Track Deleted",
                (
                    f"Track '{track_name}' "
                    "deleted successfully."
                ),
            )

            self.refresh()

        else:

            QMessageBox.warning(
                self,
                "Delete Track Failed",
                (
                    "The track could not be deleted. "
                    "Make sure the track does not contain "
                    "any assigned cars."
                ),
            )

            self.refresh()

    # ------------------------------------------------------------------
    # Add spot
    # ------------------------------------------------------------------

    def add_spot(
        self,
    ):

        track = self.get_selected_track()

        if track is None:

            QMessageBox.warning(
                self,
                "No Track Selected",
                "Select a track before adding a spot.",
            )

            return

        track_id = track.id

        dialog = AddSpotDialog(
            track=track,
            parent=self,
        )

        if (
            dialog.exec()
            != dialog.DialogCode.Accepted
        ):

            return

        data = dialog.get_data()

        try:

            SpotService.add(
                track_id=track_id,
                spot_number=data[
                    "spot_number"
                ],
                name=data[
                    "name"
                ],
                description=data[
                    "description"
                ],
                max_length=data[
                    "max_length"
                ],
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
                notes=data[
                    "notes"
                ],
            )

        except Exception as ex:

            QMessageBox.warning(
                self,
                "Add Spot Failed",
                str(ex),
            )

            self.load_spots()

            return

        #
        # Reload the spot list while keeping the
        # current track selected.
        #

        self.load_spots()

        self.update_button_state()

    # ------------------------------------------------------------------
    # Edit spot
    # ------------------------------------------------------------------

    def edit_spot(
        self,
    ):

        track = self.get_selected_track()

        if track is None:

            QMessageBox.warning(
                self,
                "No Track Selected",
                "Select a track before editing a spot.",
            )

            return

        spot = self.get_selected_spot()

        if spot is None:

            QMessageBox.warning(
                self,
                "No Spot Selected",
                "Select a spot to edit.",
            )

            return

        track_id = track.id
        spot_id = spot.id
        spot_number = spot.spot_number

        dialog = AddSpotDialog(
            spot=spot,
            track=track,
            parent=self,
        )

        if (
            dialog.exec()
            != dialog.DialogCode.Accepted
        ):

            return

        data = dialog.get_data()

        try:

            result = SpotService.update(
                spot_id=spot_id,
                name=data[
                    "name"
                ],
                description=data[
                    "description"
                ],
                max_length=data[
                    "max_length"
                ],
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
                notes=data[
                    "notes"
                ],
            )

        except Exception as ex:

            QMessageBox.warning(
                self,
                "Update Failed",
                str(ex),
            )

            self.load_spots(
                preserve_spot_id=spot_id
            )

            return

        if result:

            self.load_spots(
                preserve_spot_id=spot_id
            )

            self.update_button_state()

        else:

            QMessageBox.warning(
                self,
                "Update Failed",
                "The spot could not be updated.",
            )

            self.load_spots(
                preserve_spot_id=spot_id
            )

    # ------------------------------------------------------------------
    # Delete spot
    # ------------------------------------------------------------------

    def delete_spot(
        self,
    ):

        spot_id = (
            self.get_selected_spot_id()
        )

        if spot_id is None:

            QMessageBox.warning(
                self,
                "No Spot Selected",
                "Select a spot to delete.",
            )

            return

        #
        # Get the spot before deleting it.
        #

        spot = self.get_selected_spot()

        if spot is None:

            QMessageBox.warning(
                self,
                "Spot Not Found",
                "The selected spot could not be found.",
            )

            self.load_spots()

            return

        spot_number = spot.spot_number

        #
        # Final occupancy check before asking for
        # confirmation.
        #

        if self.is_spot_occupied(
            spot_id
        ):

            QMessageBox.warning(
                self,
                "Spot Occupied",
                (
                    "This spot contains a car "
                    "and cannot be deleted."
                ),
            )

            self.update_button_state()

            return

        answer = QMessageBox.question(
            self,
            "Delete Spot",
            (
                f"Are you sure you want to delete "
                f"Spot {spot_number}?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):

            return

        #
        # Final occupancy check immediately before
        # deletion.
        #

        if self.is_spot_occupied(
            spot_id
        ):

            QMessageBox.warning(
                self,
                "Spot Occupied",
                (
                    "This spot now contains a car "
                    "and cannot be deleted."
                ),
            )

            self.load_spots()

            return

        result = SpotService.delete(
            spot_id
        )

        if result:

            self.load_spots()

            self.update_button_state()

        else:

            QMessageBox.warning(
                self,
                "Delete Failed",
                "The spot could not be deleted.",
            )

            self.load_spots()