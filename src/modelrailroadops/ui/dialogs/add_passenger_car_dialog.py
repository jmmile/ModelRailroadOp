from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from sqlalchemy.exc import SQLAlchemyError
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from modelrailroadops.services.passenger_car_service import (
    PassengerCarService,
)
from modelrailroadops.services import passenger_image_service as images


class AddPassengerCarDialog(QDialog):
    """
    Dialog used to add or edit passenger equipment.
    """

    def __init__(
        self,
        parent=None,
        passenger_car=None,
    ):

        super().__init__(parent)

        self.passenger_car = passenger_car
        self.picture = None
        self.remove_picture = False

        self.setWindowTitle(
            "Add Passenger Car"
        )

        self.resize(
            475,
            450,
        )

        layout = QVBoxLayout(
            self
        )

        form = QFormLayout()

        self.reporting_mark = QLineEdit()

        self.number = QLineEdit()

        self.name = QLineEdit()

        self.owner = QLineEdit()

        self.equipment_type = QComboBox()

        self.equipment_type.setEditable(
            True
        )

        self.equipment_type.addItems([
            "Coach",
            "Baggage",
            "Baggage-Coach",
            "Sleeper",
            "Diner",
            "Lounge",
            "Observation",
            "Parlor",
            "RPO",
            "Express",
        ])

        self.length = QLineEdit()

        self.length.setPlaceholderText(
            "Length in feet"
        )

        self.status = QComboBox()

        self.status.addItems([
            "AVAILABLE",
            "ASSIGNED",
            "OUT_OF_SERVICE",
        ])

        self.notes = QTextEdit()

        self.notes.setPlaceholderText(
            "Optional notes"
        )

        self.notes.setMaximumHeight(
            100
        )

        form.addRow(
            "Reporting Mark",
            self.reporting_mark,
        )

        form.addRow(
            "Number",
            self.number,
        )

        form.addRow(
            "Name",
            self.name,
        )

        form.addRow(
            "Owner",
            self.owner,
        )

        form.addRow(
            "Equipment Type",
            self.equipment_type,
        )

        form.addRow(
            "Length (ft)",
            self.length,
        )

        form.addRow(
            "Status",
            self.status,
        )

        form.addRow(
            "Notes",
            self.notes,
        )

        layout.addLayout(
            form
        )

        self.picture_preview = QLabel("No Image Available")
        self.picture_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.picture_preview.setFixedSize(400, 150)
        layout.addWidget(self.picture_preview, alignment=Qt.AlignmentFlag.AlignHCenter)
        picture_buttons = QHBoxLayout()
        self.picture_button = QPushButton("Add Picture")
        self.remove_picture_button = QPushButton("Remove Picture")
        self.remove_picture_button.setEnabled(False)
        picture_buttons.addWidget(self.picture_button)
        picture_buttons.addWidget(self.remove_picture_button)
        layout.addLayout(picture_buttons)
        self.picture_button.clicked.connect(self.choose_picture)
        self.remove_picture_button.clicked.connect(self.clear_picture)
        if passenger_car:
            try:
                existing = images.find_image(passenger_car.reporting_mark, passenger_car.number)
                if existing:
                    self.show_picture(QPixmap(str(existing)))
            except (OSError, ValueError) as error:
                self.picture_preview.setText(str(error))
                self.picture_preview.setWordWrap(True)

        buttons = QHBoxLayout()

        self.save_button = QPushButton(
            "Save"
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )

        buttons.addStretch()

        buttons.addWidget(
            self.save_button
        )

        buttons.addWidget(
            self.cancel_button
        )

        layout.addLayout(
            buttons
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        self.save_button.clicked.connect(
            self.save
        )

        if self.passenger_car:

            self.reporting_mark.setText(
                self.passenger_car.reporting_mark
            )

            self.number.setText(
                self.passenger_car.number
            )

            self.name.setText(
                self.passenger_car.name or ""
            )

            self.owner.setText(
                self.passenger_car.owner or ""
            )

            self.equipment_type.setCurrentText(
                self.passenger_car.equipment_type
            )

            if self.passenger_car.length is not None:

                self.length.setText(
                    str(
                        self.passenger_car.length
                    )
                )

            self.status.setCurrentText(
                self.passenger_car.status
            )

            self.notes.setPlainText(
                self.passenger_car.notes or ""
            )

            self.setWindowTitle(
                "Edit Passenger Car"
            )

    def parse_positive_integer(
        self,
        field,
        field_name,
    ):

        value_text = (
            field.text()
            .strip()
            .replace(
                ",",
                "",
            )
        )

        if not value_text:

            return True, None

        try:

            value = int(
                value_text
            )

        except ValueError:

            QMessageBox.warning(
                self,
                "Invalid Value",
                (
                    f"{field_name} must be "
                    f"a whole number."
                ),
            )

            return False, None

        if value <= 0:

            QMessageBox.warning(
                self,
                "Invalid Value",
                (
                    f"{field_name} must be "
                    f"greater than zero."
                ),
            )

            return False, None

        return True, value

    def show_picture(self, pixmap):
        self.picture_preview.clear()
        if pixmap.isNull():
            self.picture_preview.setText("Picture cannot be displayed")
        else:
            self.picture_preview.setPixmap(pixmap.scaled(
                self.picture_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        self.picture_button.setText("Change Picture")
        self.remove_picture_button.setEnabled(True)

    def choose_picture(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Passenger Car Picture", "",
            "Pictures (*.png *.jpg *.jpeg);;PNG (*.png);;JPEG (*.jpg *.jpeg)",
        )
        if not filename:
            return
        try:
            picture = images.import_picture(filename)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Picture Error", str(error))
            return
        self.picture = picture
        self.remove_picture = False
        pixmap = QPixmap()
        pixmap.loadFromData(picture, "PNG")
        self.show_picture(pixmap)

    def clear_picture(self):
        self.picture = None
        self.remove_picture = True
        self.picture_preview.clear()
        self.picture_preview.setText("No Image Available")
        self.picture_button.setText("Add Picture")
        self.remove_picture_button.setEnabled(False)

    def save(self):
        try:
            self._save()
        except (OSError, ValueError, SQLAlchemyError) as error:
            QMessageBox.warning(self, "Unable to Save Passenger Car", str(error))

    def _save(self):

        reporting_mark = (
            self.reporting_mark.text()
            .strip()
            .upper()
        )

        number = (
            self.number.text()
            .strip()
        )

        name = (
            self.name.text()
            .strip()
        )

        owner = (
            self.owner.text()
            .strip()
        )

        equipment_type = (
            self.equipment_type.currentText()
            .strip()
        )

        status = (
            self.status.currentText()
        )

        notes = (
            self.notes.toPlainText()
            .strip()
        )

        if not reporting_mark:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a reporting mark.",
            )

            return

        if not number:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a passenger car number.",
            )

            return

        if not equipment_type:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter an equipment type.",
            )

            return

        valid, length = self.parse_positive_integer(
            self.length,
            "Length",
        )

        if not valid:

            return

        if self.passenger_car:

            updated_passenger_car = PassengerCarService.update(
                passenger_car_id=self.passenger_car.id,
                picture=self.picture,
                remove_picture=self.remove_picture,
                reporting_mark=reporting_mark,
                number=number,
                name=name,
                owner=owner,
                equipment_type=equipment_type,
                length=length,
                status=status,
                notes=notes,
            )

            if updated_passenger_car is None:

                QMessageBox.warning(
                    self,
                    "Duplicate Passenger Car",
                    (
                        "A passenger car with the same "
                        "reporting mark and number "
                        "already exists."
                    ),
                )

                return

        else:

            passenger_car = PassengerCarService.add(
                picture=self.picture,
                remove_picture=self.remove_picture,
                reporting_mark=reporting_mark,
                number=number,
                name=name,
                owner=owner,
                equipment_type=equipment_type,
                length=length,
                status=status,
                notes=notes,
            )

            if passenger_car is None:

                QMessageBox.warning(
                    self,
                    "Duplicate Passenger Car",
                    (
                        "A passenger car with the same "
                        "reporting mark and number "
                        "already exists."
                    ),
                )

                return

        self.accept()
