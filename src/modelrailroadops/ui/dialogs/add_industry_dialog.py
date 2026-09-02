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
    IndustryService,
)

from modelrailroadops.services.industry_track_service import (
    IndustryTrackService,
)

from modelrailroadops.ui.dialogs.add_industry_track_dialog import (
    AddIndustryTrackDialog,
)


class AddIndustryDialog(QDialog):
    """
    Add or edit an industry.

    A new industry is saved to the database before tracks
    can be added to it. This allows an industry with zero
    tracks to exist and be displayed by the Industry Tracks
    tab.
    """

    def __init__(
        self,
        parent=None,
        industry=None,
    ):
        super().__init__(parent)

        self.industry = industry

        if self.industry:
            self.setWindowTitle("Edit Industry")
        else:
            self.setWindowTitle("Add Industry")

        #
        # Main layout
        #

        layout = QVBoxLayout(self)

        #
        # Industry information
        #

        form = QFormLayout()

        self.name = QLineEdit()
        self.railroad = QLineEdit()
        self.location = QLineEdit()
        self.notes = QTextEdit()

        form.addRow(
            "Industry Name",
            self.name,
        )

        form.addRow(
            "Railroad",
            self.railroad,
        )

        form.addRow(
            "Location",
            self.location,
        )

        form.addRow(
            "Notes",
            self.notes,
        )

        layout.addLayout(form)

        #
        # Track table
        #

        self.track_table = QTableWidget()

        self.track_table.setColumnCount(2)

        self.track_table.setHorizontalHeaderLabels(
            [
                "Track",
                "Spots",
            ]
        )

        self.track_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.track_table.setSelectionMode(
            QTableWidget.SingleSelection
        )

        self.track_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        layout.addWidget(
            self.track_table
        )

        #
        # Buttons
        #

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

        layout.addLayout(button_layout)

        #
        # Signals
        #

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

        #
        # Update the Edit/Delete buttons whenever
        # the selected track changes.
        #

        self.track_table.itemSelectionChanged.connect(
            self.update_button_state
        )

        #
        # Initial state
        #

        if self.industry:
            self.load_industry()

        self.update_button_state()

    #
    # Load existing industry
    #

    def load_industry(self):
        """
        Load existing industry data into the dialog.
        """

        self.name.setText(
            self.industry.name or ""
        )

        self.railroad.setText(
            self.industry.railroad or ""
        )

        self.location.setText(
            self.industry.location or ""
        )

        self.notes.setPlainText(
            self.industry.notes or ""
        )

        self.load_tracks()

    #
    # Ensure industry has been saved
    #

    def ensure_saved(self):
        """
        Ensure the industry exists in the database.

        For a new industry, this method creates the industry
        immediately so tracks can be added to it before the
        dialog is finally saved/closed.

        Returns:
            True if an industry is available.
            False if the industry could not be saved.
        """

        #
        # Existing industry
        #

        if self.industry is not None:
            return True

        #
        # Validate name
        #

        name = self.name.text().strip()

        if not name:

            QMessageBox.warning(
                self,
                "Missing Name",
                "Enter an industry name first.",
            )

            return False

        #
        # Save new industry
        #

        try:

            industry = IndustryService.add(
                name=name,
                railroad=self.railroad.text().strip(),
                location=self.location.text().strip(),
                notes=self.notes.toPlainText().strip(),
            )

        except Exception as ex:

            QMessageBox.critical(
                self,
                "Save Industry Failed",
                (
                    "The industry could not be saved.\n\n"
                    f"{ex}"
                ),
            )

            return False

        #
        # Verify the service returned
        # an actual Industry object.
        #

        if industry is None:

            QMessageBox.critical(
                self,
                "Save Industry Failed",
                "The industry was not saved.",
            )

            return False

        #
        # Store the saved Industry object.
        #

        self.industry = industry

        #
        # Reload the track table.
        #

        self.load_tracks()

        self.update_button_state()

        return True

    #
    # Load tracks
    #

    def load_tracks(self):
        """
        Reload tracks belonging to the current industry.
        """

        self.track_table.setRowCount(0)

        if self.industry is None:
            self.update_button_state()
            return

        tracks = IndustryTrackService.get_by_industry(
            self.industry.id
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
                    track.name or ""
                ),
            )

            self.track_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    str(len(track.spots))
                ),
            )

        #
        # No track should remain selected after
        # rebuilding the table.
        #

        self.track_table.clearSelection()

        self.update_button_state()

    #
    # Update button state
    #

    def update_button_state(self):
        """
        Enable or disable track buttons.

        Add Track is available for both new and existing
        industries. If the industry is new, clicking Add
        Track will call ensure_saved() first.

        Edit and Delete require an existing industry and
        a selected track.
        """

        #
        # Add Track
        #
        # This must remain enabled for a new industry.
        #
        # add_track() calls ensure_saved(), which creates
        # the industry before the track is added.
        #

        self.add_track_button.setEnabled(
            True
        )

        #
        # A track can only be edited or deleted when
        # the industry has already been saved and a
        # track is selected.
        #

        industry_available = (
            self.industry is not None
        )

        track_selected = (
            industry_available
            and self.track_table.currentRow() >= 0
        )

        #
        # Edit Track
        #

        self.edit_track_button.setEnabled(
            track_selected
        )

        #
        # Delete Track
        #

        self.delete_track_button.setEnabled(
            track_selected
        )

    #
    # Add track
    #

    def add_track(self):
        """
        Add a track to the current industry.

        A new industry is saved first if necessary.
        """

        if not self.ensure_saved():
            return

        dialog = AddIndustryTrackDialog(
            parent=self
        )

        if not dialog.exec():
            return

        name = dialog.name.text().strip()

        if not name:

            QMessageBox.warning(
                self,
                "Missing Track Name",
                "Enter a track name.",
            )

            return

        try:

            result = IndustryTrackService.add(
                industry_id=self.industry.id,
                name=name,
                spots=dialog.spots.value(),
            )

        except Exception as ex:

            QMessageBox.critical(
                self,
                "Add Track Failed",
                str(ex),
            )

            return

        if result is None:

            QMessageBox.warning(
                self,
                "Add Track Failed",
                "The track could not be added.",
            )

            return

        self.load_tracks()

    #
    # Edit track
    #

    def edit_track(self):
        """
        Edit the selected industry track.
        """

        row = self.track_table.currentRow()

        if row < 0:
            return

        if self.industry is None:
            return

        tracks = IndustryTrackService.get_by_industry(
            self.industry.id
        )

        if row >= len(tracks):
            return

        track = tracks[row]

        dialog = AddIndustryTrackDialog(
            track=track,
            parent=self,
        )

        if not dialog.exec():
            return

        name = dialog.name.text().strip()

        if not name:

            QMessageBox.warning(
                self,
                "Missing Track Name",
                "Enter a track name.",
            )

            return

        result = IndustryTrackService.update(
            track.id,
            name,
            dialog.spots.value(),
        )

        if result:

            self.load_tracks()

        else:

            QMessageBox.warning(
                self,
                "Update Failed",
                (
                    "Cannot reduce the number of spots "
                    "because some spots contain cars."
                ),
            )

    #
    # Delete track
    #

    def delete_track(self):
        """
        Delete the selected industry track.
        """

        row = self.track_table.currentRow()

        if row < 0:
            return

        if self.industry is None:
            return

        tracks = IndustryTrackService.get_by_industry(
            self.industry.id
        )

        if row >= len(tracks):
            return

        track = tracks[row]

        answer = QMessageBox.question(
            self,
            "Delete Track",
            (
                f"Are you sure you want to delete "
                f"the track '{track.name}'?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        result = IndustryTrackService.delete(
            track.id
        )

        if not result:

            QMessageBox.warning(
                self,
                "Cannot Delete",
                (
                    "The track could not be deleted. "
                    "It may contain assigned cars."
                ),
            )

        self.load_tracks()

    #
    # Save
    #

    def save(self):
        """
        Save the industry and close the dialog.

        For a new industry, ensure_saved() creates it.
        For an existing industry, update() modifies it.
        """

        #
        # Existing industry
        #

        if self.industry is not None:

            name = self.name.text().strip()

            if not name:

                QMessageBox.warning(
                    self,
                    "Missing Name",
                    "Enter an industry name.",
                )

                return

            try:

                result = IndustryService.update(
                    industry_id=self.industry.id,
                    name=name,
                    railroad=self.railroad.text().strip(),
                    location=self.location.text().strip(),
                    notes=self.notes.toPlainText().strip(),
                )

            except Exception as ex:

                QMessageBox.critical(
                    self,
                    "Save Industry Failed",
                    str(ex),
                )

                return

            if result is None:

                QMessageBox.critical(
                    self,
                    "Save Industry Failed",
                    "The industry could not be updated.",
                )

                return

            self.industry = result

            self.accept()

            return

        #
        # New industry
        #

        if not self.ensure_saved():
            return

        #
        # At this point the industry definitely exists
        # in the database.
        #

        self.accept()