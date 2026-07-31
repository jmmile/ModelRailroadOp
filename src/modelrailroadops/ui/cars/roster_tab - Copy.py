from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QLineEdit,
    QLabel,
)

from modelrailroadops.services.car_service import CarService
from modelrailroadops.ui.dialogs.add_car_dialog import AddCarDialog
from modelrailroadops.models.car import Car

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
        

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.table.setColumnCount(6)

        self.table.setHorizontalHeaderLabels(
            [
                "Reporting Mark",
                "Number",
                "Owner",
                "Type",
                "Status",
                "Location",
            ]
        )

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
        

    def refresh(self):

        cars = CarService.get_all()

        self.table.setRowCount(len(cars))

        for row, car in enumerate(cars):

            item = QTableWidgetItem(car.reporting_mark)
            item.setData(Qt.UserRole, car.id)   

            self.table.setItem(
                row,
                0,
                item,
)

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(car.number),
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(car.owner),
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(car.car_type),
                
            )
            self.table.setItem(
                row,
                4,
                QTableWidgetItem(car.status),
)
            
            self.table.setItem(
                row,
                5,
                QTableWidgetItem(car.location),
            )

    def add_car(self):
        dialog = AddCarDialog(self)

        if dialog.exec():
            self.refresh()

    def edit_car(self):

        row = self.table.currentRow()

        if row == -1:
            print("No car selected")
            return

        reporting_mark = self.table.item(row, 0).text()
        number = self.table.item(row, 1).text()

        car = CarService.get_by_reporting_mark_and_number(
            reporting_mark,
            number,
        )

        if car is None:
            print("Car not found.")
            return

        dialog = AddCarDialog(self, car)

        if dialog.exec():
            self.refresh()
            
    def delete_car(self):

        row = self.table.currentRow()

        if row == -1:
            QMessageBox.information(
                self,
                "Delete Car",
                "Please select a car to delete."
            )
            return

        reporting_mark = self.table.item(row, 0).text()
        number = self.table.item(row, 1).text()

        car = CarService.get_by_reporting_mark_and_number(
            reporting_mark,
            number,
        )

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