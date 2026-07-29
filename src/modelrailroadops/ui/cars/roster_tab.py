from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from modelrailroadops.services.car_service import CarService


class RosterTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.add_button = QPushButton("Add Car")

        self.table = QTableWidget()

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

        layout.addWidget(self.add_button)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):

        cars = CarService.get_all()

        self.table.setRowCount(len(cars))

        for row, car in enumerate(cars):

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(car.reporting_mark),
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