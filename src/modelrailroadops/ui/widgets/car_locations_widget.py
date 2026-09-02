from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableView,
    QHBoxLayout,
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
)

from modelrailroadops.ui.models.car_location_table_model import (
    CarLocationTableModel,
)

from modelrailroadops.ui.dialogs.move_car_dialog import (
    MoveCarDialog,
)

from modelrailroadops.ui.dialogs.move_car_to_location_dialog import (
    MoveCarToLocationDialog,
)

from modelrailroadops.services.waybill_service import WaybillService
from modelrailroadops.services.car_location_service import CarLocationService

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)


class CarLocationsWidget(QWidget):
    """
    Displays current car locations:

    Car -> Industry -> Track -> Spot

    Provides actions to assign, move, and clear
    car locations.
    """

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.model = CarLocationTableModel()

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

        self.table.setSortingEnabled(
            True
        )

        self.table.horizontalHeader().setSortIndicatorShown(
            True
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
        # Buttons
        #

        self.assign_button = QPushButton(
            "Assign Car"
        )

        self.move_button = QPushButton(
            "Move Car"
        )

        self.clear_button = QPushButton(
            "Clear Location"
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        button_layout = QHBoxLayout()

        button_layout.addWidget(
            self.assign_button
        )

        button_layout.addWidget(
            self.move_button
        )

        button_layout.addWidget(
            self.clear_button
        )

        button_layout.addWidget(
            self.refresh_button
        )

        button_layout.addStretch()

        #
        # Main layout
        #

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            self.table
        )

        layout.addLayout(
            button_layout
        )

        #
        # Button signals
        #

        self.assign_button.clicked.connect(
            self.assign_car
        )

        self.move_button.clicked.connect(
            self.move_car
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.clear_button.clicked.connect(
            self.clear_location
        )

        #
        # Initial load
        #

        self.refresh()

    #
    # Refresh
    #

    def refresh(
        self,
    ):
        """
        Reload car location data.
        """

        selected_car_id = self.get_selected_car_id()

        self.model.load_data()

        self.table.resizeColumnsToContents()

        if selected_car_id is None:

            return

        row_number = self.model.find_row_by_car_id(
            selected_car_id
        )

        if row_number is None:

            return

        index = self.model.index(
            row_number,
            0,
        )

        self.table.setCurrentIndex(
            index
        )

        self.table.selectRow(
            row_number
        )

    #
    # Get selected car ID
    #

    def get_selected_car_id(
        self,
    ):
        """
        Return the database ID of the currently
        selected car.
        """

        index = (
            self.table.currentIndex()
        )

        if not index.isValid():

            return None

        return self.model.get_car_id(
            index.row()
        )

    #
    # Assign car
    #

    def assign_car(
        self,
    ):
        """
        Assign the selected unassigned car to a destination.
        """

        car_id = self.get_selected_car_id()

        if car_id is None:
            QMessageBox.warning(
                self,
                "No Car Selected",
                "Please select a car before clicking Assign Car.",
            )
            return

        location = CarLocationService.get_car_location(
            car_id
        )

        if location is None:
            QMessageBox.warning(
                self,
                "Assign Car",
                "The selected car could not be found.",
            )
            return

        already_assigned = any(
            (
                location.get("industry"),
                location.get("operating_location"),
                location.get("track"),
                location.get("spot"),
            )
        )

        if already_assigned:
            QMessageBox.information(
                self,
                "Car Already Assigned",
                "This car already has a location. Use Move Car instead.",
            )
            return

        dialog = MoveCarToLocationDialog(
            car_id=car_id,
            parent=self,
            assignment=True,
        )

        if dialog.exec():

            self.refresh()

    #
    # Move car
    #

    def move_car(
        self,
    ):
        """
        Open the Move Car dialog for the
        currently selected car.
        """

        car_id = (
            self.get_selected_car_id()
        )

        if car_id is None:

            QMessageBox.warning(
                self,
                "No Car Selected",
                (
                    "Please select a car "
                    "before clicking Move Car."
                )
            )

            return

        active_waybills = WaybillService.get_active_for_car(
            car_id
        )

        if active_waybills:
            dialog = MoveCarDialog(
                car_id=car_id,
                parent=self,
            )
        else:
            dialog = MoveCarToLocationDialog(
                car_id=car_id,
                parent=self,
            )

        if dialog.exec():

            self.refresh()

    def clear_location(self):
        car_id = self.get_selected_car_id()

        if car_id is None:
            QMessageBox.warning(
                self,
                "No Car Selected",
                "Please select a car before clearing its location.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Clear Car Location",
            "Clear the selected car's current location?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        if not CarLocationService.clear_car_location(car_id):
            QMessageBox.warning(
                self,
                "Clear Car Location",
                "The car location could not be cleared.",
            )
            return

        self.refresh()
