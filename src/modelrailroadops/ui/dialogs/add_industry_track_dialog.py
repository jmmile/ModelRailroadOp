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
    """
    Dialog used for adding and editing
    industry tracks.
    """

    def __init__(
        self,
        track=None,
        parent=None,
    ):
        super().__init__(parent)

        self.track = track


        if self.track:
            self.setWindowTitle(
                "Edit Industry Track"
            )
        else:
            self.setWindowTitle(
                "Add Industry Track"
            )


        self.resize(
            350,
            150
        )


        layout = QVBoxLayout(
            self
        )


        form = QFormLayout()


        self.name = QLineEdit()


        self.spots = QSpinBox()

        self.spots.setMinimum(
            1
        )

        self.spots.setMaximum(
            999
        )

        self.spots.setValue(
            4
        )


        form.addRow(
            "Track Name",
            self.name
        )

        form.addRow(
            "Number of Spots",
            self.spots
        )


        layout.addLayout(
            form
        )


        button_layout = QHBoxLayout()


        self.ok_button = QPushButton(
            "Add"
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )


        button_layout.addStretch()


        button_layout.addWidget(
            self.ok_button
        )

        button_layout.addWidget(
            self.cancel_button
        )


        layout.addLayout(
            button_layout
        )


        self.ok_button.clicked.connect(
            self.accept
        )

        self.cancel_button.clicked.connect(
            self.reject
        )


        if self.track:
            self.load_track()



    def load_track(self):
        """
        Populate fields from an existing track.
        """

        self.name.setText(
            self.track.name
        )


        self.spots.setValue(
            len(self.track.spots)
        )


        self.ok_button.setText(
            "Save"
        )