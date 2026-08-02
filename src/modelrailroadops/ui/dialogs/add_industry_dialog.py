from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
        
)


from modelrailroadops.services.industry_track_service import IndustryTrackService

from modelrailroadops.services.industry_service import IndustryService

from modelrailroadops.ui.dialogs.add_industry_track_dialog import (
    AddIndustryTrackDialog
)


class AddIndustryDialog(QDialog):

    def __init__(self, parent=None, industry=None):
        super().__init__(parent)

        self.industry = industry

        self.setWindowTitle("Add Industry")
        self.resize(500, 350)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name = QLineEdit()
        self.railroad = QLineEdit()
        self.location = QLineEdit()
       
        self.notes = QTextEdit()

        form.addRow("Industry Name", self.name)
        form.addRow("Railroad", self.railroad)
        form.addRow("Location", self.location)
        form.addRow("Notes", self.notes)

        layout.addLayout(form)
        self.track_table = QTableWidget()
        self.track_table.setColumnCount(2)
        self.track_table.setHorizontalHeaderLabels(
            ["Track Name", "Spots"]
        )

        self.track_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.Stretch
        )

        layout.addWidget(self.track_table)

        track_buttons = QHBoxLayout()

        self.add_track_button = QPushButton("Add Track")
        self.delete_track_button = QPushButton("Delete Track")

        track_buttons.addWidget(self.add_track_button)
        track_buttons.addWidget(self.delete_track_button)
        track_buttons.addStretch()

        layout.addLayout(track_buttons)




        buttons = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        buttons.addStretch()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)
        

        layout.addLayout(buttons)

        if self.industry:

            self.name.setText(self.industry.name)
            self.railroad.setText(self.industry.railroad)
            self.location.setText(self.industry.location)
            self.notes.setPlainText(self.industry.notes)
            self.load_tracks()
            
            self.setWindowTitle("Edit Industry")

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save)
        
             
        self.add_track_button.clicked.connect(
            self.add_track
        )

        self.delete_track_button.clicked.connect(
            self.delete_track
        )
        
        self.track_table.doubleClicked.connect(
            self.edit_track
        )
        
        
    def load_tracks(self):

        tracks = IndustryTrackService.get_by_industry(
            self.industry.id
        )

        self.track_table.setRowCount(0)

        for track in tracks:

            row = self.track_table.rowCount()
            self.track_table.insertRow(row)

            self.track_table.setItem(
                row,
                0,
                QTableWidgetItem(track.name)
            )

            self.track_table.setItem(
                row,
                1,
                QTableWidgetItem(str(track.spots))
            )

    def add_track(self):

        # If this is a new industry, save it first so it gets an ID
        if self.industry is None:

            self.industry = IndustryService.add(
                name=self.name.text().strip(),
                railroad=self.railroad.text().strip(),
                location=self.location.text().strip(),
                notes=self.notes.toPlainText().strip(),
            )

            self.setWindowTitle("Edit Industry")

        dialog = AddIndustryTrackDialog(self)

        if dialog.exec():

            IndustryTrackService.add(
                industry_id=self.industry.id,
                name=dialog.name.text().strip(),
                spots=dialog.spots.value(),
            )

            self.load_tracks()

    def edit_track(self):
        
        if not self.industry:
            return

        row = self.track_table.currentRow()

        if row < 0:
            return

        tracks = IndustryTrackService.get_by_industry(
            self.industry.id
        )

        if row >= len(tracks):
            return
        
        track = tracks[row]
        
        print("Selected track:", track.name, track.spots)

        dialog = AddIndustryTrackDialog(self, track)

        if dialog.exec():

            IndustryTrackService.update(
                track_id=tracks[row].id,
                name=dialog.name.text().strip(),
                spots=dialog.spots.value(),
            )

            self.load_tracks()

       
    def delete_track(self):

        if not self.industry:
            return

        row = self.track_table.currentRow()

        if row < 0:
            return

        tracks = IndustryTrackService.get_by_industry(
            self.industry.id
        )

        if row >= len(tracks):
            return

        IndustryTrackService.delete(
            tracks[row].id
        )

        self.load_tracks()   


    def save(self):

        if self.industry:

            IndustryService.update(
                industry_id=self.industry.id,
                name=self.name.text().strip(),
                railroad=self.railroad.text().strip(),
                location=self.location.text().strip(),
                notes=self.notes.toPlainText().strip(),
            )

        else:

            self.industry = IndustryService.add(
                name=self.name.text().strip(),
                railroad=self.railroad.text().strip(),
                location=self.location.text().strip(),
                notes=self.notes.toPlainText().strip(),
            )

        self.accept()