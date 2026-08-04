from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableView,
    QHBoxLayout,
    QMessageBox,
)

from modelrailroadops.ui.models.industry_track_table_model import (
    IndustryTrackTableModel
)

from modelrailroadops.ui.dialogs.add_industry_track_dialog import (
    AddIndustryTrackDialog
)

from modelrailroadops.services.industry_track_service import (
    IndustryTrackService
)


class IndustryTracksWidget(QWidget):
    """
    Displays and manages industry tracks.
    """

    def __init__(self):
        super().__init__()


        self.model = IndustryTrackTableModel()


        self.table = QTableView()

        self.table.setModel(
            self.model
        )


        self.table.setSelectionBehavior(
            QTableView.SelectRows
        )

        self.table.setSelectionMode(
            QTableView.SingleSelection
        )


        self.add_button = QPushButton(
            "Add Track"
        )

        self.edit_button = QPushButton(
            "Edit Track"
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )


        button_layout = QHBoxLayout()

        button_layout.addWidget(
            self.add_button
        )

        button_layout.addWidget(
            self.edit_button
        )

        button_layout.addWidget(
            self.refresh_button
        )

        button_layout.addStretch()


        layout = QVBoxLayout()

        layout.addWidget(
            self.table
        )

        layout.addLayout(
            button_layout
        )


        self.setLayout(
            layout
        )


        self.add_button.clicked.connect(
            self.add_track
        )

        self.edit_button.clicked.connect(
            self.edit_track
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )


        self.refresh()



    def refresh(self):

        self.model.refresh()

        self.table.resizeColumnsToContents()



    def add_track(self):
        """
        Add a new industry track.
        """

        selected = self.table.currentIndex()


        if not selected.isValid():

            QMessageBox.warning(
                self,
                "No Industry Selected",
                "Select an industry before adding a track."
            )

            return



        industry = (
            self.model.tracks[selected.row()].industry
        )


        dialog = AddIndustryTrackDialog(
            parent=self
        )


        if dialog.exec():

            IndustryTrackService.add(
                industry_id=industry.id,
                name=dialog.name.text().strip(),
                spots=dialog.spots.value(),
            )

            self.refresh()



    def edit_track(self):
        """
        Edit the selected industry track.
        """

        index = (
            self.table.currentIndex()
        )


        if not index.isValid():

            QMessageBox.warning(
                self,
                "No Track Selected",
                "Select a track to edit."
            )

            return



        track = (
            self.model.tracks[index.row()]
        )


        dialog = AddIndustryTrackDialog(
            track=track,
            parent=self
        )


        if dialog.exec():

            result = IndustryTrackService.update(
                track.id,
                dialog.name.text().strip(),
                dialog.spots.value(),
            )


            if result:

                self.refresh()

            else:

                QMessageBox.warning(
                    self,
                    "Update Failed",
                    "Cannot reduce spots because some spots contain cars."
                )