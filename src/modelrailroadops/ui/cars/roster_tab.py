from PySide6.QtCore import Qt, QSortFilterProxyModel

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

from modelrailroadops.services.car_service import CarService

from modelrailroadops.ui.dialogs.add_car_dialog import (
    AddCarDialog
)

from modelrailroadops.ui.cars.car_table_model import (
    CarTableModel
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE
)



class RosterTab(QWidget):

    def __init__(self):

        super().__init__()


        layout = QVBoxLayout(self)


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
            "Reporting Mark, Number, Owner, Type, Status, Location..."
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
        # Table
        #

        self.table = QTableView()


        self.table.setModel(
            self.proxy
        )


        # Apply highlight AFTER model assignment
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


        self.refresh()



    def refresh(self):

        self.model.refresh()

        self.table.resizeColumnsToContents()


        total = self.model.rowCount()


        self.status_label.setText(
            f"{total} Cars"
        )



    def add_car(self):

        dialog = AddCarDialog(
            self
        )

        if dialog.exec():

            self.refresh()



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


        dialog = AddCarDialog(
            self,
            car
        )


        if dialog.exec():

            self.refresh()



    def delete_car(self):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )


        if not indexes:

            return


        source_index = self.proxy.mapToSource(
            indexes[0]
        )


        car = self.model.get_car(
            source_index.row()
        )


        if car:

            CarService.delete(
                car.id
            )

            self.refresh()



    def export_csv(self):

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Roster",
            "",
            "CSV Files (*.csv)"
        )


        if filepath:

            self.model.export_to_csv(
                filepath
            )



    def import_csv(self):

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Roster",
            "",
            "CSV Files (*.csv)"
        )


        if filepath:

            self.model.import_from_csv(
                filepath
            )

            self.refresh()