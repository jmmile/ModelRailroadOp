from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
)


class AddIndustryTrackDialog(QDialog):

    def __init__(self, parent=None, track=None):
        super().__init__(parent)

        self.track = track

        self.setWindowTitle("Add Track")
        self.resize(300, 150)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name = QLineEdit()

        self.spots = QSpinBox()
        self.spots.setMinimum(1)
        self.spots.setMaximum(999)

        form.addRow("Track Name", self.name)
        form.addRow("Car Spots", self.spots)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        buttons.addStretch()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(buttons)

        if self.track:
            self.name.setText(self.track.name)
            self.spots.setValue(self.track.spots)

            self.setWindowTitle("Edit Track")

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)