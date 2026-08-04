from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QMessageBox,
)

from modelrailroadops.services.industry_service import (
    IndustryService
)

from modelrailroadops.services.industry_track_service import (
    IndustryTrackService
)

from modelrailroadops.ui.dialogs.add_industry_track_dialog import (
    AddIndustryTrackDialog
)


class AddIndustryDialog(QDialog):
    """
    Add or edit an industry.
    """

    def __init__(
        self,
        parent=None,
        industry=None,
    ):
        super().__init__(parent)

        self.industry = industry


        self.setWindowTitle(
            "Add Industry"
        )


        layout = QVBoxLayout(
            self
        )


        form = QFormLayout()


        self.name = QLineEdit()
        self.railroad = QLineEdit()
        self.location = QLineEdit()
        self.notes = QTextEdit()


        form.addRow(
            "Industry Name",
            self.name
        )

        form.addRow(
            "Railroad",
            self.railroad
        )

        form.addRow(
            "Location",
            self.location
        )

        form.addRow(
            "Notes",
            self.notes
        )


        layout.addLayout(
            form
        )


        self.track_table = QTableWidget()

        self.track_table.setColumnCount(
            2
        )

        self.track_table.setHorizontalHeaderLabels(
            [
                "Track",
                "Spots",
            ]
        )


        layout.addWidget(
            self.track_table
        )


        button_layout = QHBoxLayout()


        self.add_track_button = QPushButton(
            "Add Track"
        )

        self.edit_track_button = QPushButton(
            "Edit Track"
        )

        self.delete_track_button = QPushButton(
            "Delete Track"
        )

        self.save_button = QPushButton(
            "Save"
        )


        button_layout.addWidget(
            self.add_track_button
        )

        button_layout.addWidget(
            self.edit_track_button
        )

        button_layout.addWidget(
            self.delete_track_button
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.save_button
        )


        layout.addLayout(
            button_layout
        )


        self.add_track_button.clicked.connect(
            self.add_track
        )

        self.edit_track_button.clicked.connect(
            self.edit_track
        )

        self.delete_track_button.clicked.connect(
            self.delete_track
        )

        self.save_button.clicked.connect(
            self.save
        )


        if self.industry:

            self.load_industry()



    def load_industry(self):
        """
        Load existing industry data.
        """

        self.name.setText(
            self.industry.name
        )

        self.railroad.setText(
            self.industry.railroad
        )

        self.location.setText(
            self.industry.location
        )

        self.notes.setPlainText(
            self.industry.notes or ""
        )

        self.load_tracks()



    def ensure_saved(self):
        """
        Save a new industry before adding tracks.
        """

        if self.industry:
            return True


        if not self.name.text().strip():

            QMessageBox.warning(
                self,
                "Missing Name",
                "Enter an industry name first."
            )

            return False


        self.industry = IndustryService.add(
            name=self.name.text().strip(),
            railroad=self.railroad.text().strip(),
            location=self.location.text().strip(),
            notes=self.notes.toPlainText(),
        )


        return True



    def load_tracks(self):

        if not self.industry:
            return


        tracks = IndustryTrackService.get_by_industry(
            self.industry.id
        )


        self.track_table.setRowCount(
            0
        )


        for track in tracks:

            row = self.track_table.rowCount()

            self.track_table.insertRow(
                row
            )


            self.track_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    track.name
                )
            )


            self.track_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    str(len(track.spots))
                )
            )



    def add_track(self):

        if not self.ensure_saved():
            return


        dialog = AddIndustryTrackDialog(
            parent=self
        )


        if dialog.exec():

            IndustryTrackService.add(
                industry_id=self.industry.id,
                name=dialog.name.text().strip(),
                spots=dialog.spots.value(),
            )


            self.load_tracks()



    def edit_track(self):

        row = self.track_table.currentRow()

        if row < 0:
            return


        tracks = IndustryTrackService.get_by_industry(
            self.industry.id
        )


        track = tracks[row]


        dialog = AddIndustryTrackDialog(
            track=track,
            parent=self
        )


        if dialog.exec():

            IndustryTrackService.update(
                track.id,
                dialog.name.text().strip(),
                dialog.spots.value(),
            )


            self.load_tracks()



    def delete_track(self):

        row = self.track_table.currentRow()

        if row < 0:
            return


        tracks = IndustryTrackService.get_by_industry(
            self.industry.id
        )


        track = tracks[row]


        if not IndustryTrackService.delete(
            track.id
        ):

            QMessageBox.warning(
                self,
                "Cannot Delete",
                "Track contains assigned cars."
            )


        self.load_tracks()



    def save(self):

        if self.industry:

            IndustryService.update(
                industry_id=self.industry.id,
                name=self.name.text().strip(),
                railroad=self.railroad.text().strip(),
                location=self.location.text().strip(),
                notes=self.notes.toPlainText(),
            )

        else:

            self.ensure_saved()


        self.accept()