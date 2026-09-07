from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from modelrailroadops.services.location_service import LocationService
from modelrailroadops.ui.dialogs.add_location_dialog import AddLocationDialog
from modelrailroadops.ui.dialogs.add_location_track_dialog import (
    AddLocationTrackDialog,
)
from modelrailroadops.ui.styles import TABLE_SELECTION_STYLE


class LocationsWidget(QWidget):
    """
    Manage general railroad locations and their operational tracks.

    Freight Industry locations exist in the general Location system
    because they are used by routing and other operational features,
    but they are managed through the Freight Industries and
    Industry Tracks tabs.

    The Locations tab therefore displays only non-industry railroad
    locations such as stations, yards, staging, interchanges, and
    other operating points.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.locations = []
        self.tracks = []

        layout = QVBoxLayout(self)

        location_buttons = QHBoxLayout()
        self.add_location_button = QPushButton("Add Location")
        self.edit_location_button = QPushButton("Edit Location")
        self.delete_location_button = QPushButton("Delete Location")
        self.activate_location_button = QPushButton("Activate")
        self.deactivate_location_button = QPushButton("Deactivate")
        self.refresh_button = QPushButton("Refresh")

        for button in (
            self.add_location_button,
            self.edit_location_button,
            self.delete_location_button,
            self.activate_location_button,
            self.deactivate_location_button,
            self.refresh_button,
        ):
            location_buttons.addWidget(button)

        location_buttons.addStretch()
        layout.addLayout(location_buttons)

        self.location_status = QLabel()
        layout.addWidget(self.location_status)

        self.location_model = QStandardItemModel(self)
        self.location_model.setHorizontalHeaderLabels(
            [
                "Name",
                "Type",
                "Tracks",
                "Status",
                "Notes",
            ]
        )

        self.location_table = QTableView()
        self._configure_table(
            self.location_table,
            self.location_model,
        )

        track_area = QWidget()
        track_layout = QVBoxLayout(track_area)
        track_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.track_label = QLabel("Tracks")
        track_layout.addWidget(
            self.track_label
        )

        track_buttons = QHBoxLayout()
        self.add_track_button = QPushButton(
            "Add Track"
        )
        self.edit_track_button = QPushButton(
            "Edit Track"
        )
        self.delete_track_button = QPushButton(
            "Delete Track"
        )

        for button in (
            self.add_track_button,
            self.edit_track_button,
            self.delete_track_button,
        ):
            track_buttons.addWidget(button)

        track_buttons.addStretch()
        track_layout.addLayout(
            track_buttons
        )

        self.track_model = QStandardItemModel(self)
        self.track_model.setHorizontalHeaderLabels(
            [
                "Track",
                "Type",
                "Traffic Use",
                "Car Capacity",
                "Status",
                "Notes",
            ]
        )

        self.track_table = QTableView()
        self._configure_table(
            self.track_table,
            self.track_model,
        )
        track_layout.addWidget(
            self.track_table
        )

        splitter = QSplitter(
            Qt.Vertical
        )
        splitter.setChildrenCollapsible(
            False
        )
        splitter.addWidget(
            self.location_table
        )
        splitter.addWidget(
            track_area
        )
        splitter.setSizes(
            [
                430,
                300,
            ]
        )
        layout.addWidget(
            splitter
        )

        self.add_location_button.clicked.connect(
            self.add_location
        )
        self.edit_location_button.clicked.connect(
            self.edit_location
        )
        self.delete_location_button.clicked.connect(
            self.delete_location
        )
        self.activate_location_button.clicked.connect(
            lambda: self.set_location_active(
                True
            )
        )
        self.deactivate_location_button.clicked.connect(
            lambda: self.set_location_active(
                False
            )
        )
        self.refresh_button.clicked.connect(
            self.refresh
        )
        self.add_track_button.clicked.connect(
            self.add_track
        )
        self.edit_track_button.clicked.connect(
            self.edit_track
        )
        self.delete_track_button.clicked.connect(
            self.delete_track
        )
        self.location_table.doubleClicked.connect(
            self.edit_location
        )
        self.track_table.doubleClicked.connect(
            self.edit_track
        )
        self.location_table.selectionModel().selectionChanged.connect(
            self.location_selection_changed
        )
        self.track_table.selectionModel().selectionChanged.connect(
            self.update_buttons
        )

        self.refresh()

    @staticmethod
    def _configure_table(
        table,
        model,
    ):
        table.setModel(
            model
        )
        table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        table.setAlternatingRowColors(
            True
        )
        table.setSortingEnabled(
            True
        )
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        table.horizontalHeader().setStretchLastSection(
            True
        )
        table.verticalHeader().setVisible(
            False
        )

    @staticmethod
    def _row_items(
        values,
        record_id,
    ):
        items = []

        for value in values:
            item = QStandardItem()

            item.setData(
                (
                    ""
                    if value is None
                    else value
                ),
                Qt.DisplayRole,
            )

            item.setEditable(
                False
            )

            items.append(
                item
            )

        if items:
            items[0].setData(
                record_id,
                Qt.UserRole,
            )

        return items

    def refresh(self):
        selected_id = (
            self.get_selected_location_id()
        )

        all_locations = list(
            LocationService.get_all()
        )

        #
        # Industry locations remain in the general Location
        # system for routing and operational relationships,
        # but they are managed through Freight Industries.
        #
        # The Locations tab is reserved for stations, yards,
        # staging, interchanges, and other general locations.
        #

        self.locations = [
            location
            for location in all_locations
            if (
                location.location_type or ""
            ).strip().upper()
            != "INDUSTRY"
        ]

        self.location_model.removeRows(
            0,
            self.location_model.rowCount(),
        )

        for location in self.locations:
            self.location_model.appendRow(
                self._row_items(
                    [
                        location.name,
                        location.location_type.title(),
                        len(
                            location.tracks
                        ),
                        (
                            "Active"
                            if location.active
                            else "Inactive"
                        ),
                        location.notes or "",
                    ],
                    location.id,
                )
            )

        self.location_status.setText(
            f"{len(self.locations)} locations"
        )

        row_to_select = (
            0
            if self.locations
            else None
        )

        if selected_id is not None:
            for row in range(
                self.location_model.rowCount()
            ):
                item = (
                    self.location_model.item(
                        row,
                        0,
                    )
                )

                if (
                    item is not None
                    and item.data(
                        Qt.UserRole
                    )
                    == selected_id
                ):
                    row_to_select = row
                    break

        if row_to_select is not None:
            self.location_table.selectRow(
                row_to_select
            )
        else:
            self.load_tracks()

        self.update_buttons()

    def get_selected_location(
        self,
    ):
        rows = (
            self.location_table
            .selectionModel()
            .selectedRows()
        )

        if not rows:
            return None

        row = rows[0].row()

        item = self.location_model.item(
            row,
            0,
        )

        location_id = (
            item.data(
                Qt.UserRole
            )
            if item is not None
            else None
        )

        return next(
            (
                location
                for location in self.locations
                if location.id
                == location_id
            ),
            None,
        )

    def get_selected_location_id(
        self,
    ):
        location = (
            self.get_selected_location()
        )

        return (
            location.id
            if location is not None
            else None
        )

    def get_selected_track(
        self,
    ):
        rows = (
            self.track_table
            .selectionModel()
            .selectedRows()
        )

        if not rows:
            return None

        row = rows[0].row()

        item = self.track_model.item(
            row,
            0,
        )

        track_id = (
            item.data(
                Qt.UserRole
            )
            if item is not None
            else None
        )

        return next(
            (
                track
                for track in self.tracks
                if track.id
                == track_id
            ),
            None,
        )

    def location_selection_changed(
        self,
        selected=None,
        deselected=None,
    ):
        self.load_tracks()
        self.update_buttons()

    def load_tracks(
        self,
    ):
        location = (
            self.get_selected_location()
        )

        self.tracks = (
            list(
                location.tracks
            )
            if location is not None
            else []
        )

        self.track_model.removeRows(
            0,
            self.track_model.rowCount(),
        )

        if location is None:
            self.track_label.setText(
                "Tracks"
            )
        else:
            self.track_label.setText(
                f"Tracks — {location.name}"
            )

        for track in self.tracks:
            self.track_model.appendRow(
                self._row_items(
                    [
                        track.name,
                        track.track_type.title(),
                        track.traffic_use.title(),
                        (
                            track.capacity
                            if track.capacity
                            is not None
                            else ""
                        ),
                        (
                            "Active"
                            if track.active
                            else "Inactive"
                        ),
                        track.notes or "",
                    ],
                    track.id,
                )
            )

    def update_buttons(
        self,
        selected=None,
        deselected=None,
    ):
        location = (
            self.get_selected_location()
        )

        track = (
            self.get_selected_track()
        )

        has_location = (
            location is not None
        )

        industry_location = (
            bool(
                location.industries
            )
            if location
            else False
        )

        linked_industry_track = (
            bool(
                track.industry_tracks
            )
            if track
            else False
        )

        self.edit_location_button.setEnabled(
            has_location
        )

        self.delete_location_button.setEnabled(
            has_location
            and not industry_location
        )

        self.activate_location_button.setEnabled(
            has_location
            and not location.active
        )

        self.deactivate_location_button.setEnabled(
            has_location
            and location.active
        )

        self.add_track_button.setEnabled(
            has_location
            and not industry_location
        )

        self.edit_track_button.setEnabled(
            track is not None
            and not linked_industry_track
        )

        self.delete_track_button.setEnabled(
            track is not None
            and not linked_industry_track
        )

    def add_location(
        self,
    ):
        dialog = AddLocationDialog(
            self
        )

        if (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        ):
            self.refresh()

    def edit_location(
        self,
        index=None,
    ):
        location = (
            self.get_selected_location()
        )

        if location is None:
            return

        dialog = AddLocationDialog(
            self,
            location,
        )

        if (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        ):
            self.refresh()

    def set_location_active(
        self,
        active,
    ):
        location = (
            self.get_selected_location()
        )

        if location is None:
            return

        success, result = (
            LocationService.set_active(
                location.id,
                active,
            )
        )

        if not success:
            QMessageBox.warning(
                self,
                "Location",
                str(
                    result
                ),
            )
            return

        self.refresh()

    def delete_location(
        self,
    ):
        location = (
            self.get_selected_location()
        )

        if location is None:
            return

        answer = QMessageBox.question(
            self,
            "Delete Location",
            (
                f"Delete location "
                f"'{location.name}'?\n\n"
                f"Its "
                f"{len(location.tracks)} "
                f"general track(s) "
                f"will also be deleted.\n\n"
                f"This cannot be undone."
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if (
            answer
            != QMessageBox.Yes
        ):
            return

        success, result = (
            LocationService.delete(
                location.id
            )
        )

        if not success:
            QMessageBox.warning(
                self,
                "Delete Location",
                str(
                    result
                ),
            )
            return

        self.refresh()

    def add_track(
        self,
    ):
        location = (
            self.get_selected_location()
        )

        if location is None:
            return

        dialog = (
            AddLocationTrackDialog(
                location,
                self,
            )
        )

        if (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        ):
            self.refresh()

    def edit_track(
        self,
        index=None,
    ):
        location = (
            self.get_selected_location()
        )

        track = (
            self.get_selected_track()
        )

        if (
            location is None
            or track is None
        ):
            return

        dialog = (
            AddLocationTrackDialog(
                location,
                self,
                track,
            )
        )

        if (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        ):
            self.refresh()

    def delete_track(
        self,
    ):
        track = (
            self.get_selected_track()
        )

        if track is None:
            return

        answer = QMessageBox.question(
            self,
            "Delete Location Track",
            f"Delete track '{track.name}'?",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if (
            answer
            != QMessageBox.Yes
        ):
            return

        success, result = (
            LocationService.delete_track(
                track.id
            )
        )

        if not success:
            QMessageBox.warning(
                self,
                "Location Track",
                str(
                    result
                ),
            )
            return

        self.refresh()