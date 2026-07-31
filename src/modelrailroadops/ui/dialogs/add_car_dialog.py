from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
)

from modelrailroadops.services.car_service import CarService


class AddCarDialog(QDialog):

    def __init__(self, parent=None, car=None):
        super().__init__(parent)

        self.car = car

        self.setWindowTitle("Add Freight Car")
        self.resize(400, 250)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.reporting_mark = QLineEdit()
        self.number = QLineEdit()
        self.owner = QLineEdit()

        self.car_type = QComboBox()
        self.car_type.addItems([
            "Boxcar",
            "Covered Hopper",
            "Flat Car",
            "Tank Car",
            "Gondola",
            "Hopper",
            "Centerbeam",
            "Autorack",
            "Intermodal",
            "Caboose",
            "MoW",
            "Passenger",
            "HiCube",
            "Depressed Flatcar",
            "Other",
        ])

        self.status = QComboBox()
        self.status.addItems([
            "Available",
            "Loaded",
            "Empty",
            "In Shop",
            "Interchange Track",
        ])

        self.location = QLineEdit()

        form.addRow("Reporting Mark", self.reporting_mark)
        form.addRow("Number", self.number)
        form.addRow("Owner", self.owner)
        form.addRow("Car Type", self.car_type)
        form.addRow("Status", self.status)
        form.addRow("Location", self.location)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        buttons.addStretch()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(buttons)

        # Populate the fields when editing
        if self.car:
            self.reporting_mark.setText(self.car.reporting_mark)
            self.number.setText(self.car.number)
            self.owner.setText(self.car.owner)
            self.car_type.setCurrentText(self.car.car_type)
            self.status.setCurrentText(self.car.status)
            self.location.setText(self.car.location)

            self.setWindowTitle("Edit Freight Car")

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save)

    def save(self):

        if self.car:

            CarService.update(
                car_id=self.car.id,
                reporting_mark=self.reporting_mark.text().strip(),
                number=self.number.text().strip(),
                owner=self.owner.text().strip(),
                car_type=self.car_type.currentText(),
                status=self.status.currentText(),
                location=self.location.text().strip(),
            )

        else:

            CarService.add(
                reporting_mark=self.reporting_mark.text().strip(),
                number=self.number.text().strip(),
                owner=self.owner.text().strip(),
                car_type=self.car_type.currentText(),
                status=self.status.currentText(),
                location=self.location.text().strip(),
            )

        self.accept()