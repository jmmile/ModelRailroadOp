from PySide6.QtCore import Qt, QSortFilterProxyModel
from modelrailroadops.ui.cars.car_table_model import CarTableModel
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableView,
    QMessageBox,
    QLineEdit,
    QLabel,
)


from modelrailroadops.ui.dialogs.add_car_dialog import AddCarDialog


class RosterTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        
        self.search_label = QLabel("Search")

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
                "Reporting Mark, Number, Owner, Type, Status, Location..."
)

        self.add_button = QPushButton("Add Car")
        self.edit_button = QPushButton("Edit Car")
        self.delete_button = QPushButton("Delete Car")
        

        self.model = CarTableModel()

        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        
        self.proxy.setFilterCaseSensitivity(
            Qt.CaseInsensitive
)

        self.proxy.setFilterKeyColumn(-1)
        
        self.search_box.textChanged.connect(
        self.proxy.setFilterFixedString
)
        

        self.table = QTableView()

        self.table.setModel(self.proxy)
        
        from PySide6.QtWidgets import QHeaderView
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)

        self.table.setSelectionBehavior(
            QTableView.SelectRows
)

        self.table.setSelectionMode(
            QTableView.SingleSelection
)

        self.table.setAlternatingRowColors(True)

        
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_box)

        layout.addWidget(self.add_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.table)

        self.refresh()
        self.add_button.clicked.connect(self.add_car)
        self.edit_button.clicked.connect(self.edit_car)
        self.delete_button.clicked.connect(self.delete_car)
        self.table.doubleClicked.connect(self.edit_car)
        

    def refresh(self):
        self.model.refresh()
       

    def add_car(self):
        dialog = AddCarDialog(self)

        if dialog.exec():
            self.refresh()

    def edit_car(self, index=None):

        indexes = self.table.selectionModel().selectedRows()

        if not indexes:
            QMessageBox.information(
                self,
                "Edit Car",
                "Please select a car."
        )
        return

        proxy_index = indexes[0]
        source_index = self.proxy.mapToSource(proxy_index)

        car = self.model.cars[source_index.row()]

        dialog = AddCarDialog(self, car)

        if dialog.exec():
            self.refresh()

        if car is None:
            print("Car not found.")
            return

        dialog = AddCarDialog(self, car)

        if dialog.exec():
            self.refresh()
            
def delete_car(self):

    indexes = self.table.selectionModel().selectedRows()

    if not indexes:
        QMessageBox.information(
            self,
            "Delete Car",
            "Please select a car."
        )
        return

    proxy_index = indexes[0]
    source_index = self.proxy.mapToSource(proxy_index)

    car = self.model.cars[source_index.row()]

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

        if car is None:
            QMessageBox.warning(
                self,
                "Delete Car",
                "The selected car could not be found."
            )
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