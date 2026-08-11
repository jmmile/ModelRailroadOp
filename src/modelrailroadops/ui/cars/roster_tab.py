
from PySide6.QtCore import (
    Qt,
    QSortFilterProxyModel,
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableView,
    QMessageBox,
    QLineEdit,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QFileDialog,
)

from modelrailroadops.services.car_service import (
    CarService,
)

from modelrailroadops.ui.dialogs.add_car_dialog import (
    AddCarDialog,
)

from modelrailroadops.ui.cars.car_table_model import (
    CarTableModel,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)


class RosterTab(QWidget):
    """
    Displays and manages the freight car roster.
    """

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

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
            QLabel("Search")
        )

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            "Reporting Mark, Number, Owner, Type, "
            "Status, Location..."
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
            "Add Car"
        )

        self.edit_button = QPushButton(
            "Edit Car"
        )

        self.delete_button = QPushButton(
            "Delete Car"
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

        self.model = CarTableModel()

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

        #
        # Sort using displayed text.
        #
        # This allows Type to sort alphabetically
        # without changing the actual car_type values
        # stored in the database.
        #

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
            self.add_car
        )

        self.edit_button.clicked.connect(
            self.edit_car
        )

        self.delete_button.clicked.connect(
            self.delete_car
        )

        self.import_button.clicked.connect(
            self.import_csv
        )

        self.export_button.clicked.connect(
            self.export_csv
        )

        self.table.doubleClicked.connect(
            self.edit_car
        )

        #
        # Initial load
        #

        self.refresh()

        #
        # Start the roster sorted by Car Type.
        #

        self.proxy.sort(
            3,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            3,
            Qt.AscendingOrder
        )

    #
    # Refresh when the tab becomes visible
    #

    def showEvent(self, event):

        super().showEvent(
            event
        )

        #
        # Reload the roster from the database
        # every time the user returns to the tab.
        #
        # This is important because cars can be
        # assigned, moved, or released from other
        # tabs while this model still contains
        # older Car objects.
        #

        self.refresh()

        #
        # Keep the roster sorted by Car Type.
        #

        self.proxy.sort(
            3,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            3,
            Qt.AscendingOrder
        )

    #
    # Refresh
    #

    def refresh(self):

        self.model.refresh()

        #
        # Re-evaluate the proxy model.
        #

        self.proxy.invalidate()

        #
        # Resize columns after the model changes.
        #

        self.table.resizeColumnsToContents()

        #
        # Update roster count.
        #

        total = self.model.rowCount()

        self.status_label.setText(
            f"{total} Cars"
        )

    #
    # Add car
    #

    def add_car(self):

        dialog = AddCarDialog(
            self
        )

        if dialog.exec():

            self.refresh()

            self.proxy.sort(
                3,
                Qt.AscendingOrder
            )

    #
    # Edit car
    #

    def edit_car(
        self,
        index=None
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Edit Car",
                "Please select a car."
            )

            return

        source_index = self.proxy.mapToSource(
            indexes[0]
        )

        car = self.model.get_car(
            source_index.row()
        )

        if car is None:

            return

        dialog = AddCarDialog(
            self,
            car
        )

        if dialog.exec():

            self.refresh()

            self.proxy.sort(
                3,
                Qt.AscendingOrder
            )

    #
    # Delete car
    #

    def delete_car(self):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Delete Car",
                "Please select a car."
            )

            return

        source_index = self.proxy.mapToSource(
            indexes[0]
        )

        car = self.model.get_car(
            source_index.row()
        )

        if car is None:

            return

        result = QMessageBox.question(
            self,
            "Delete Car",
            (
                f"Are you sure you want to delete "
                f"{car.reporting_mark} {car.number}?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:

            return

        CarService.delete(
            car.id
        )

        self.refresh()

        self.proxy.sort(
            3,
            Qt.AscendingOrder
        )

    #
    # Export CSV
    #

    def export_csv(self):

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Roster",
            "",
            "CSV Files (*.csv)"
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
                "The car roster was exported successfully."
            )

        except Exception as ex:

            QMessageBox.warning(
                self,
                "Export Failed",
                str(ex)
            )

    #
    # Import CSV
    #

    def import_csv(self):

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Roster",
            "",
            "CSV Files (*.csv)"
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
                str(ex)
            )

            return

        #
        # Refresh through the normal UI path.
        #

        self.refresh()

        #
        # Reapply Type sorting after import.
        #

        self.proxy.sort(
            3,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            3,
            Qt.AscendingOrder
        )

        total = self.model.rowCount()

        QMessageBox.information(
            self,
            "Import Complete",
            (
                f"Imported: {added}\n"
                f"Skipped: {skipped}\n\n"
                f"Roster now contains {total} cars."
            )
        )
