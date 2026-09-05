from PySide6.QtCore import (
    Qt,
    QSortFilterProxyModel,
)

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from modelrailroadops.services.passenger_car_service import (
    PassengerCarService,
)

from modelrailroadops.ui.dialogs.add_passenger_car_dialog import (
    AddPassengerCarDialog,
)

from modelrailroadops.ui.passenger_cars.passenger_car_table_model import (
    PassengerCarTableModel,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)


class PassengerCarsWidget(QWidget):
    """
    Displays and manages the passenger equipment roster.
    """

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        layout = QVBoxLayout(
            self
        )

        #
        # Status
        #

        self.status_label = QLabel()

        layout.addWidget(
            self.status_label
        )

        #
        # Search
        #

        search_layout = QHBoxLayout()

        search_layout.addWidget(
            QLabel(
                "Search"
            )
        )

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            (
                "Reporting Mark, Number, Name, Owner, "
                "Equipment Type, Length, Capacity, Status..."
            )
        )

        search_layout.addWidget(
            self.search_box
        )

        layout.addLayout(
            search_layout
        )

        #
        # Buttons
        #

        button_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "Add Passenger Car"
        )

        self.edit_button = QPushButton(
            "Edit Passenger Car"
        )

        self.delete_button = QPushButton(
            "Delete Passenger Car"
        )

        self.import_button = QPushButton(
            "Import CSV"
        )

        self.export_button = QPushButton(
            "Export CSV"
        )

        button_layout.addWidget(
            self.add_button
        )

        button_layout.addWidget(
            self.edit_button
        )

        button_layout.addWidget(
            self.delete_button
        )

        button_layout.addWidget(
            self.import_button
        )

        button_layout.addWidget(
            self.export_button
        )

        button_layout.addStretch()

        layout.addLayout(
            button_layout
        )

        #
        # Model
        #

        self.model = PassengerCarTableModel()

        self.proxy = QSortFilterProxyModel(
            self
        )

        self.proxy.setSourceModel(
            self.model
        )

        self.proxy.setFilterCaseSensitivity(
            Qt.CaseInsensitive
        )

        self.proxy.setFilterKeyColumn(
            -1
        )

        self.proxy.setSortRole(
            Qt.DisplayRole
        )

        #
        # Table
        #

        self.table = QTableView()

        self.table.setModel(
            self.proxy
        )

        self.table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.table.setFocusPolicy(
            Qt.StrongFocus
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

        self.table.setSortingEnabled(
            True
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        layout.addWidget(
            self.table
        )

        #
        # Signals
        #

        self.search_box.textChanged.connect(
            self.proxy.setFilterRegularExpression
        )

        self.add_button.clicked.connect(
            self.add_passenger_car
        )

        self.edit_button.clicked.connect(
            self.edit_passenger_car
        )

        self.delete_button.clicked.connect(
            self.delete_passenger_car
        )

        self.import_button.clicked.connect(
            self.import_csv
        )

        self.export_button.clicked.connect(
            self.export_csv
        )

        self.table.doubleClicked.connect(
            self.edit_passenger_car
        )

        #
        # Initial load
        #

        self.refresh()

        self.proxy.sort(
            0,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            0,
            Qt.AscendingOrder
        )

    def showEvent(
        self,
        event,
    ):

        super().showEvent(
            event
        )

        self.refresh()

        self.proxy.sort(
            0,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            0,
            Qt.AscendingOrder
        )

    def refresh(self):

        self.model.refresh()

        self.proxy.invalidate()

        self.table.resizeColumnsToContents()

        total = self.model.rowCount()

        self.status_label.setText(
            f"{total} Passenger Cars"
        )

    def selected_passenger_car(self):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            return None

        source_index = self.proxy.mapToSource(
            indexes[0]
        )

        return self.model.get_passenger_car(
            source_index.row()
        )

    def add_passenger_car(self):

        dialog = AddPassengerCarDialog(
            self
        )

        if dialog.exec():

            self.refresh()

            self.proxy.sort(
                0,
                Qt.AscendingOrder
            )

    def edit_passenger_car(
        self,
        index=None,
    ):

        passenger_car = self.selected_passenger_car()

        if passenger_car is None:

            QMessageBox.information(
                self,
                "Edit Passenger Car",
                "Please select a passenger car.",
            )

            return

        dialog = AddPassengerCarDialog(
            self,
            passenger_car,
        )

        if dialog.exec():

            self.refresh()

            self.proxy.sort(
                0,
                Qt.AscendingOrder
            )

    def delete_passenger_car(self):

        passenger_car = self.selected_passenger_car()

        if passenger_car is None:

            QMessageBox.information(
                self,
                "Delete Passenger Car",
                "Please select a passenger car.",
            )

            return

        result = QMessageBox.question(
            self,
            "Delete Passenger Car",
            (
                f"Are you sure you want to delete "
                f"{passenger_car.reporting_mark} "
                f"{passenger_car.number}?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:

            return

        deleted = PassengerCarService.delete(
            passenger_car.id
        )

        if not deleted:

            QMessageBox.warning(
                self,
                "Delete Passenger Car",
                "The passenger car could not be deleted.",
            )

            return

        self.refresh()

        self.proxy.sort(
            0,
            Qt.AscendingOrder
        )

    def export_csv(self):

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Passenger Equipment Roster",
            "",
            "CSV Files (*.csv)",
        )

        if not filepath:

            return

        try:

            self.model.export_to_csv(
                filepath
            )

            QMessageBox.information(
                self,
                "Export Complete",
                (
                    "The passenger equipment roster was "
                    "exported successfully."
                ),
            )

        except Exception as ex:

            QMessageBox.warning(
                self,
                "Export Failed",
                str(ex),
            )

    def import_csv(self):

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Passenger Equipment Roster",
            "",
            "CSV Files (*.csv)",
        )

        if not filepath:

            return

        try:

            added, skipped = (
                self.model.import_from_csv(
                    filepath
                )
            )

        except Exception as ex:

            QMessageBox.critical(
                self,
                "Import Failed",
                str(ex),
            )

            return

        self.refresh()

        self.proxy.sort(
            0,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            0,
            Qt.AscendingOrder
        )

        total = self.model.rowCount()

        QMessageBox.information(
            self,
            "Import Complete",
            (
                f"Imported: {added}\n"
                f"Skipped: {skipped}\n\n"
                f"Roster now contains "
                f"{total} passenger cars."
            ),
        )