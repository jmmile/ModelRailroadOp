from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from modelrailroadops.services.location_service import LocationService


class AddLocationTrackDialog(QDialog):
    def __init__(self, location, parent=None, track=None):
        super().__init__(parent)

        self.location = location
        self.track = track
        self.setWindowTitle("Edit Location Track" if track else "Add Location Track")
        self.resize(450, 320)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(LocationService.TRACK_TYPES)
        self.traffic_use_combo = QComboBox()
        self.traffic_use_combo.addItems(LocationService.TRAFFIC_USES)
        self.traffic_use_combo.setCurrentText("BOTH")
        self.capacity_edit = QSpinBox()
        self.capacity_edit.setRange(0, 9999)
        self.capacity_edit.setSpecialValueText("Not set")
        self.notes_edit = QTextEdit()
        self.active_checkbox = QCheckBox("Track is active")
        self.active_checkbox.setChecked(True)

        form.addRow("Location:", QLineEdit(location.name))
        location_field = form.itemAt(form.rowCount() - 1, QFormLayout.FieldRole).widget()
        location_field.setReadOnly(True)
        form.addRow("Track Name:", self.name_edit)
        form.addRow("Track Type:", self.type_combo)
        form.addRow("Traffic Use:", self.traffic_use_combo)
        form.addRow("Car Capacity:", self.capacity_edit)
        form.addRow("Notes:", self.notes_edit)
        form.addRow("Status:", self.active_checkbox)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if track is not None:
            self.name_edit.setText(track.name or "")
            type_index = self.type_combo.findText(track.track_type)
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)
            traffic_index = self.traffic_use_combo.findText(
                track.traffic_use
            )
            if traffic_index >= 0:
                self.traffic_use_combo.setCurrentIndex(traffic_index)
            self.capacity_edit.setValue(track.capacity or 0)
            self.notes_edit.setPlainText(track.notes or "")
            self.active_checkbox.setChecked(bool(track.active))

    def save(self):
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Location Track", "Track name is required.")
            self.name_edit.setFocus()
            return

        arguments = {
            "location_id": self.location.id,
            "name": name,
            "track_type": self.type_combo.currentText(),
            "traffic_use": self.traffic_use_combo.currentText(),
            "capacity": self.capacity_edit.value() or None,
            "notes": self.notes_edit.toPlainText().strip(),
            "active": self.active_checkbox.isChecked(),
        }

        if self.track is None:
            success, result = LocationService.create_track(**arguments)
        else:
            success, result = LocationService.update_track(
                track_id=self.track.id,
                **arguments,
            )

        if not success:
            QMessageBox.warning(self, "Location Track", str(result))
            return

        self.accept()
