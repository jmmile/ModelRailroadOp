#```python
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QTableView,
    QPushButton,
    QHeaderView,
    QAbstractItemView,
    QSplitter,
    QMessageBox,
)

from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack

from modelrailroadops.services.car_location_service import (
    CarLocationService,
)

from modelrailroadops.ui.models.spot_occupancy_table_model import (
    SpotOccupancyTableModel,
)

from modelrailroadops.ui.dialogs.assign_car_dialog import (
    AssignCarDialog,
)

from modelrailroadops.ui.dialogs.move_car_dialog import (
    MoveCarDialog,
)

from modelrailroadops.ui.widgets.spot_detail_widget import (
    SpotDetailWidget,
)

from modelrailroadops.ui.styles import TABLE_SELECTION_STYLE


class SpotOccupancyWidget(QWidget):
    """
    Displays spot occupancy and manages car movements.

    Spot creation, editing, and deletion are handled by
    IndustryTracksWidget.
    """

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(parent)

        layout = QVBoxLayout(self)

        #
        # Filters
        #

        filter_layout = QHBoxLayout()

        filter_layout.addWidget(
            QLabel("Industry:")
        )

        self.industry_combo = QComboBox()

        filter_layout.addWidget(
            self.industry_combo
        )

        filter_layout.addWidget(
            QLabel("Track:")
        )

        self.track_combo = QComboBox()

        filter_layout.addWidget(
            self.track_combo
        )

        self.occupied_only = QCheckBox(
            "Occupied Only"
        )

        self.empty_only = QCheckBox(
            "Empty Only"
        )

        filter_layout.addWidget(
            self.occupied_only
        )

        filter_layout.addWidget(
            self.empty_only
        )

        filter_layout.addStretch()

        layout.addLayout(
            filter_layout
        )

        #
        # Main area
        #

        splitter = QSplitter()

        #
        # Spot occupancy table
        #

        self.table = QTableView()

        self.table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.model = SpotOccupancyTableModel()

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

        splitter.addWidget(
            self.table
        )

        #
        # Spot details panel
        #

        self.detail_widget = SpotDetailWidget()

        splitter.addWidget(
            self.detail_widget
        )

        splitter.setStretchFactor(
            0,
            4
        )

        splitter.setStretchFactor(
            1,
            1
        )

        layout.addWidget(
            splitter
        )

        #
        # Car operation buttons
        #

        button_layout = QHBoxLayout()

        self.assign_button = QPushButton(
            "Assign Car"
        )

        self.move_button = QPushButton(
            "Move Car"
        )

        self.remove_button = QPushButton(
            "Remove Car"
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        button_layout.addWidget(
            self.assign_button
        )

        button_layout.addWidget(
            self.move_button
        )

        button_layout.addWidget(
            self.remove_button
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.refresh_button
        )

        layout.addLayout(
            button_layout
        )

        #
        # Signals
        #

        self.industry_combo.currentIndexChanged.connect(
            self.industry_changed
        )

        self.track_combo.currentIndexChanged.connect(
            self.apply_filters
        )

        self.occupied_only.toggled.connect(
            self.occupied_changed
        )

        self.empty_only.toggled.connect(
            self.empty_changed
        )

        self.refresh_button.clicked.connect(
            self.apply_filters
        )

        self.assign_button.clicked.connect(
            self.assign_car
        )

        self.move_button.clicked.connect(
            self.move_car
        )

        self.remove_button.clicked.connect(
            self.remove_car
        )

        self.table.selectionModel().selectionChanged.connect(
            self.selection_changed
        )

        #
        # Initial load
        #

        self.load_industries()

        self.load_tracks()

        self.apply_filters()

    #
    # Selection
    #

    def selection_changed(
        self,
        selected=None,
        deselected=None,
    ):

        row = self.get_selected_row()

        if row:

            self.detail_widget.set_spot(
                row["spot_id"]
            )

        else:

            self.detail_widget.clear()

    #
    # Industry loading
    #

    def load_industries(self):

        self.industry_combo.blockSignals(True)

        self.industry_combo.clear()

        self.industry_combo.addItem(
            "All Industries",
            None
        )

        with SessionLocal() as session:

            industries = (
                session.execute(
                    select(Industry)
                    .order_by(
                        Industry.name
                    )
                )
                .scalars()
                .all()
            )

            for industry in industries:

                self.industry_combo.addItem(
                    industry.name,
                    industry.id
                )

        self.industry_combo.blockSignals(False)

    #
    # Track loading
    #

    def load_tracks(self):

        self.track_combo.blockSignals(True)

        self.track_combo.clear()

        self.track_combo.addItem(
            "All Tracks",
            None
        )

        industry_id = (
            self.industry_combo.currentData()
        )

        with SessionLocal() as session:

            query = select(
                IndustryTrack
            )

            if industry_id is not None:

                query = query.where(
                    IndustryTrack.industry_id
                    == industry_id
                )

            tracks = (
                session.execute(
                    query.order_by(
                        IndustryTrack.name
                    )
                )
                .scalars()
                .all()
            )

            for track in tracks:

                self.track_combo.addItem(
                    track.name,
                    track.id
                )

        self.track_combo.blockSignals(False)

    #
    # Industry changed
    #

    def industry_changed(self):

        self.load_tracks()

        self.apply_filters()

    #
    # Apply filters
    #

    def apply_filters(self):

        self.model.load_data(
            industry_id=(
                self.industry_combo.currentData()
            ),

            track_id=(
                self.track_combo.currentData()
            ),

            occupied_only=(
                self.occupied_only.isChecked()
            ),

            empty_only=(
                self.empty_only.isChecked()
            ),
        )

        self.table.resizeColumnsToContents()

        self.selection_changed()

    #
    # Occupied filter
    #

    def occupied_changed(
        self,
        checked,
    ):

        if checked:

            self.empty_only.setChecked(
                False
            )

        self.apply_filters()

    #
    # Empty filter
    #

    def empty_changed(
        self,
        checked,
    ):

        if checked:

            self.occupied_only.setChecked(
                False
            )

        self.apply_filters()

    #
    # Get selected row
    #

    def get_selected_row(self):

        index = self.table.currentIndex()

        if not index.isValid():

            return None

        if index.row() >= len(
            self.model.rows
        ):

            return None

        return self.model.rows[
            index.row()
        ]

    #
    # Assign car
    #

    def assign_car(self):

        row = self.get_selected_row()

        if row is None:

            QMessageBox.information(
                self,
                "No Spot Selected",
                "Please select a spot."
            )

            return

        if row.get("car_id") is not None:

            QMessageBox.information(
                self,
                "Spot Occupied",
                "This spot already contains a car."
            )

            return

        dialog = AssignCarDialog(
            spot_id=row["spot_id"],
            parent=self,
        )

        if dialog.exec():

            self.apply_filters()

    #
    # Move car
    #

    def move_car(self):

        row = self.get_selected_row()

        if row is None:

            QMessageBox.information(
                self,
                "No Spot Selected",
                "Please select a spot."
            )

            return

        car_id = row.get(
            "car_id"
        )

        if car_id is None:

            QMessageBox.information(
                self,
                "No Car",
                "The selected spot does not contain a car."
            )

            return

        dialog = MoveCarDialog(
            car_id,
            self
        )

        if dialog.exec():

            self.apply_filters()

    #
    # Remove car
    #

    def remove_car(self):

        row = self.get_selected_row()

        if row is None:

            QMessageBox.information(
                self,
                "No Spot Selected",
                "Please select a spot."
            )

            return

        car_id = row.get(
            "car_id"
        )

        if car_id is None:

            QMessageBox.information(
                self,
                "No Car",
                "The selected spot does not contain a car."
            )

            return

        result = QMessageBox.question(
            self,
            "Remove Car",
            (
                "Remove the car from this spot?\n\n"
                "The car will remain in the roster "
                "but will become unassigned."
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:

            return

        try:

            success = (
                CarLocationService.clear_car_location(
                    car_id
                )
            )

        except Exception as ex:

            QMessageBox.warning(
                self,
                "Remove Car Failed",
                str(ex)
            )

            return

        if success:

            self.apply_filters()

        else:

            QMessageBox.warning(
                self,
                "Remove Car Failed",
                "The car location could not be cleared."
            )
