from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from modelrailroadops.services.locomotive_service import (
    LocomotiveService,
)


class AddLocomotiveDialog(QDialog):
    """
    Dialog used to add or edit a locomotive.
    """

    def __init__(
        self,
        parent=None,
        locomotive=None,
    ):

        super().__init__(parent)

        self.locomotive = locomotive

        self.setWindowTitle(
            "Add Locomotive"
        )

        self.resize(
            475,
            525,
        )

        layout = QVBoxLayout(
            self
        )

        form = QFormLayout()

        self.reporting_mark = QLineEdit()

        self.number = QLineEdit()

        self.owner = QLineEdit()

        self.model = QLineEdit()

        self.manufacturer = QComboBox()

        self.manufacturer.setEditable(
            True
        )

        self.manufacturer.addItems([
            "",
            "ALCO",
            "Baldwin",
            "EMD",
            "GE",
            "Lima",
            "MPI",
            "Siemens",
        ])

        self.locomotive_type = QComboBox()

        self.locomotive_type.addItems([
            "Diesel",
            "Electric",
            "Steam",
        ])

        self.horsepower = QLineEdit()

        self.horsepower.setPlaceholderText(
            "Horsepower"
        )

        self.dcc_address = QLineEdit()

        self.dcc_address.setPlaceholderText(
            "DCC decoder address"
        )

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
            "Owner",
            self.owner,
        )

        form.addRow(
            "Model",
            self.model,
        )

        form.addRow(
            "Manufacturer",
            self.manufacturer,
        )

        form.addRow(
            "Locomotive Type",
            self.locomotive_type,
        )

        form.addRow(
            "Horsepower",
            self.horsepower,
        )

        form.addRow(
            "DCC Decoder Address",
            self.dcc_address,
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

        if self.locomotive:

            self.reporting_mark.setText(
                self.locomotive.reporting_mark
            )

            self.number.setText(
                self.locomotive.number
            )

            self.owner.setText(
                self.locomotive.owner or ""
            )

            self.model.setText(
                self.locomotive.model or ""
            )

            self.manufacturer.setCurrentText(
                self.locomotive.manufacturer or ""
            )

            self.locomotive_type.setCurrentText(
                self.locomotive.locomotive_type
            )

            if self.locomotive.horsepower is not None:

                self.horsepower.setText(
                    str(
                        self.locomotive.horsepower
                    )
                )

            if self.locomotive.dcc_address is not None:

                self.dcc_address.setText(
                    str(
                        self.locomotive.dcc_address
                    )
                )

            if self.locomotive.length is not None:

                self.length.setText(
                    str(
                        self.locomotive.length
                    )
                )

            self.status.setCurrentText(
                self.locomotive.status
            )

            self.notes.setPlainText(
                self.locomotive.notes or ""
            )

            self.setWindowTitle(
                "Edit Locomotive"
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

    def save(self):

        reporting_mark = (
            self.reporting_mark.text()
            .strip()
            .upper()
        )

        number = (
            self.number.text()
            .strip()
        )

        owner = (
            self.owner.text()
            .strip()
        )

        model = (
            self.model.text()
            .strip()
        )

        manufacturer = (
            self.manufacturer.currentText()
            .strip()
        )

        locomotive_type = (
            self.locomotive_type.currentText()
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
                "Please enter a locomotive number.",
            )

            return

        valid, horsepower = self.parse_positive_integer(
            self.horsepower,
            "Horsepower",
        )

        if not valid:

            return

        valid, dcc_address = self.parse_positive_integer(
            self.dcc_address,
            "DCC Decoder Address",
        )

        if not valid:

            return

        valid, length = self.parse_positive_integer(
            self.length,
            "Length",
        )

        if not valid:

            return

        if self.locomotive:

            updated_locomotive = LocomotiveService.update(
                locomotive_id=self.locomotive.id,
                reporting_mark=reporting_mark,
                number=number,
                owner=owner,
                model=model,
                manufacturer=manufacturer,
                locomotive_type=locomotive_type,
                horsepower=horsepower,
                dcc_address=dcc_address,
                length=length,
                status=status,
                notes=notes,
            )

            if updated_locomotive is None:

                QMessageBox.warning(
                    self,
                    "Duplicate Locomotive",
                    (
                        "A locomotive with the same "
                        "reporting mark and number "
                        "already exists."
                    ),
                )

                return

        else:

            locomotive = LocomotiveService.add(
                reporting_mark=reporting_mark,
                number=number,
                owner=owner,
                model=model,
                manufacturer=manufacturer,
                locomotive_type=locomotive_type,
                horsepower=horsepower,
                dcc_address=dcc_address,
                length=length,
                status=status,
                notes=notes,
            )

            if locomotive is None:

                QMessageBox.warning(
                    self,
                    "Duplicate Locomotive",
                    (
                        "A locomotive with the same "
                        "reporting mark and number "
                        "already exists."
                    ),
                )

                return

        self.accept()