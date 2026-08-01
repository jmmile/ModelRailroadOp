from email import header

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
from modelrailroadops.ui.dialogs.add_car_dialog import AddCarDialog
from modelrailroadops.ui.cars.car_table_model import CarTableModel


class RosterTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "Reporting Mark, Number, Owner, Type, Status, Location..."
        )
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Car")
        self.edit_button = QPushButton("Edit Car")
        self.delete_button = QPushButton("Delete Car")
        self.import_button = QPushButton("Import CSV")
        self.export_button = QPushButton("Export CSV")

        self.add_button.setShortcut("Ctrl+N")
        self.edit_button.setShortcut("Ctrl+E")
        self.delete_button.setShortcut("Delete")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Model
        self.model = CarTableModel()
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)

        # Table
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #self.table.verticalHeader().setVisible(False)
        #layout.addWidget(self.table)

# --- Column width control goes HERE ---
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)

        self.table.setColumnWidth(0, 80)    # Reporting Mark
        self.table.setColumnWidth(1, 100)   # Number
        self.table.setColumnWidth(2, 180)   # Owner
        self.table.setColumnWidth(3, 140)   # Type
        self.table.setColumnWidth(4, 140)   # Status
# -------------------------------------

        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)


        # Signals
        self.search_box.textChanged.connect(self.proxy.setFilterRegularExpression)
        self.add_button.clicked.connect(self.add_car)
        self.edit_button.clicked.connect(self.edit_car)
        self.delete_button.clicked.connect(self.delete_car)
        self.import_button.clicked.connect(self.import_csv)
        self.export_button.clicked.connect(self.export_csv)
        self.table.doubleClicked.connect(self.edit_car)

        # Initial refresh
        self.refresh()

    def refresh(self):
        self.model.refresh()
        self.table.resizeColumnsToContents()
        total = self.model.rowCount()
        loaded = sum(1 for car in self.model.cars if car.status == "Loaded")
        empty = sum(1 for car in self.model.cars if car.status == "Empty")
        in_shop = sum(1 for car in self.model.cars if car.status == "In Shop")
        interchange = sum(1 for car in self.model.cars if car.status == "Interchange Track")
                          
        self.status_label.setText(
        f"{total} Cars | 🔵 {loaded} Loaded | 🟡 {empty} Empty | 🔴 {in_shop} In Shop | 🟣 {interchange} Interchange"
)
                                 
    def add_car(self):
        dialog = AddCarDialog(self)
        if dialog.exec():
            self.refresh()

    def edit_car(self, index=None):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.information(self, "Edit Car", "Please select a car.")
            return
        proxy_index = indexes[0]
        source_index = self.proxy.mapToSource(proxy_index)
        car = self.model.get_car(source_index.row())
        if car is None:
            return
        dialog = AddCarDialog(self, car)
        if dialog.exec():
            self.refresh()

    def delete_car(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.information(self, "Delete Car", "Please select a car.")
            return
        proxy_index = indexes[0]
        source_index = self.proxy.mapToSource(proxy_index)
        car = self.model.get_car(source_index.row())
        if car is None:
            return
        answer = QMessageBox.question(
            self,
            "Delete Freight Car",
            f"Delete {car.reporting_mark} {car.number}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            CarService.delete(car.id)
            self.refresh()

    # --- NEW METHODS FOR CSV IMPORT/EXPORT ---
    def export_csv(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Roster to CSV", "", "CSV Files (*.csv)"
        )
        if filepath:
            self.model.export_to_csv(filepath)
            QMessageBox.information(self, "Export CSV", f"Roster exported to {filepath}")

    def import_csv(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Roster from CSV", "", "CSV Files (*.csv)"
        )
        if filepath:
            self.model.import_from_csv(filepath)
            QMessageBox.information(self, "Import CSV", f"Roster imported from {filepath}")
            self.refresh()
