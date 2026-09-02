from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from modelrailroadops.services.location_service import LocationService


class AddLocationDialog(QDialog):
    def __init__(self, parent=None, location=None):
        super().__init__(parent)

        self.location = location
        self.setWindowTitle("Edit Location" if location else "Add Location")
        self.resize(450, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(LocationService.LOCATION_TYPES)
        self.notes_edit = QTextEdit()
        self.active_checkbox = QCheckBox("Location is active")
        self.active_checkbox.setChecked(True)

        form.addRow("Name:", self.name_edit)
        form.addRow("Location Type:", self.type_combo)
        form.addRow("Notes:", self.notes_edit)
        form.addRow("Status:", self.active_checkbox)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if location is not None:
            self.name_edit.setText(location.name or "")
            type_index = self.type_combo.findText(location.location_type)
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)
            self.notes_edit.setPlainText(location.notes or "")
            self.active_checkbox.setChecked(bool(location.active))

            if location.industries:
                self.name_edit.setReadOnly(True)
                self.type_combo.setEnabled(False)

    def save(self):
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Location", "Location name is required.")
            self.name_edit.setFocus()
            return

        arguments = {
            "name": name,
            "location_type": self.type_combo.currentText(),
            "notes": self.notes_edit.toPlainText().strip(),
            "active": self.active_checkbox.isChecked(),
        }

        if self.location is None:
            success, result = LocationService.create(**arguments)
        else:
            success, result = LocationService.update(
                location_id=self.location.id,
                **arguments,
            )

        if not success:
            QMessageBox.warning(self, "Location", str(result))
            return

        self.accept()

