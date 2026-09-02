
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QGroupBox,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot

from modelrailroadops.services.car_location_service import (
    CarLocationService,
)


class AssignCarDialog(QDialog):
    """
    Dialog used to assign an unassigned car to a spot.

    The destination is selected by:

        Industry
            -> Track
                -> Spot

    Only unassigned cars that satisfy the selected
    spot's restrictions are displayed.

    All final validation is performed by
    CarLocationService.
    """

    def __init__(
        self,
        spot_id=None,
        industry_id=None,
        parent=None,
    ):

        super().__init__(parent)

        self.fixed_spot_id = spot_id
        self.fixed_industry_id = industry_id

        self.selected_spot_id = None

        self.setWindowTitle(
            "Assign Car"
        )

        self.resize(
            500,
            400
        )

        #
        # Main layout
        #

        layout = QVBoxLayout(
            self
        )

        #
        # Destination form
        #

        form = QFormLayout()

        self.car_combo = QComboBox()

        self.industry_combo = QComboBox()

        self.track_combo = QComboBox()

        self.spot_combo = QComboBox()

        #
        # Car
        #

        form.addRow(
            "Car",
            self.car_combo
        )

        #
        # Destination
        #

        if self.fixed_spot_id is None:

            form.addRow(
                "Industry",
                self.industry_combo
            )

            form.addRow(
                "Track",
                self.track_combo
            )

            form.addRow(
                "Spot",
                self.spot_combo
            )

        else:

            self.destination_label = QLabel(
                "Loading..."
            )

            form.addRow(
                "Destination",
                self.destination_label
            )

        layout.addLayout(
            form
        )

        #
        # Car information
        #

        info_group = QGroupBox(
            "Car Information"
        )

        info_form = QFormLayout()

        self.reporting_mark_label = QLabel(
            "-"
        )

        self.car_type_label = QLabel(
            "-"
        )

        self.length_label = QLabel(
            "-"
        )

        self.owner_label = QLabel(
            "-"
        )

        self.status_label = QLabel(
            "-"
        )

        self.location_label = QLabel(
            "-"
        )

        info_form.addRow(
            "Car",
            self.reporting_mark_label
        )

        info_form.addRow(
            "Type",
            self.car_type_label
        )

        info_form.addRow(
            "Length",
            self.length_label
        )

        info_form.addRow(
            "Owner",
            self.owner_label
        )

        info_form.addRow(
            "Status",
            self.status_label
        )

        info_form.addRow(
            "Current Location",
            self.location_label
        )

        info_group.setLayout(
            info_form
        )

        layout.addWidget(
            info_group
        )

        #
        # Buttons
        #

        buttons = QHBoxLayout()

        self.assign_button = QPushButton(
            "Assign"
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )

        buttons.addStretch()

        buttons.addWidget(
            self.assign_button
        )

        buttons.addWidget(
            self.cancel_button
        )

        layout.addLayout(
            buttons
        )

        #
        # Signals
        #

        self.assign_button.clicked.connect(
            self.assign_car
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        self.car_combo.currentIndexChanged.connect(
            self.update_car_information
        )

        #
        # Destination signals
        #

        if self.fixed_spot_id is None:

            self.industry_combo.currentIndexChanged.connect(
                self.load_tracks
            )

            self.track_combo.currentIndexChanged.connect(
                self.load_spots
            )

            self.spot_combo.currentIndexChanged.connect(
                self.spot_changed
            )

        #
        # Disable assignment until a valid
        # destination and eligible car exist.
        #

        self.assign_button.setEnabled(
            False
        )

        #
        # Initial data.
        #

        if self.fixed_spot_id is not None:

            #
            # The fixed destination is already known,
            # so load it first and then load only cars
            # eligible for that spot.
            #

            self.load_fixed_destination()

        else:

            self.load_industries(
                self.fixed_industry_id
            )

            self.load_tracks()

    # ==========================================================
    # LOAD CARS FOR A SPECIFIC SPOT
    # ==========================================================

    def load_cars_for_spot(
        self,
        spot_id,
    ):
        """
        Load only unassigned cars that satisfy all
        restrictions for the specified spot.

        This is intentionally delegated to
        CarLocationService so the UI and final
        assignment use the same validation rules.
        """

        self.car_combo.blockSignals(
            True
        )

        self.car_combo.clear()

        #
        # No destination means there is no way to
        # determine which cars are eligible.
        #

        if spot_id is None:

            self.car_combo.addItem(
                "Select an available destination spot",
                None,
            )

            self.car_combo.blockSignals(
                False
            )

            self.clear_car_information()

            self.assign_button.setEnabled(
                False
            )

            return

        #
        # Get cars that satisfy the spot restrictions.
        #

        cars = (
            CarLocationService.get_eligible_cars_for_spot(
                spot_id
            )
        )

        for car in cars:

            car_type = (
                car.car_type
                if car.car_type
                else "Unknown"
            )

            display_text = (
                f"{car.reporting_mark} "
                f"{car.number} — "
                f"{car_type}"
            )

            self.car_combo.addItem(
                display_text,
                car.id
            )

        self.car_combo.blockSignals(
            False
        )

        #
        # Cars are available.
        #

        if self.car_combo.count():

            self.car_combo.setCurrentIndex(
                0
            )

            self.update_car_information()

            self.assign_button.setEnabled(
                True
            )

            return

        #
        # No eligible cars.
        #

        self.clear_car_information()

        self.assign_button.setEnabled(
            False
        )

        #
        # Add an informational item so the user
        # understands why the list is empty.
        #

        self.car_combo.blockSignals(
            True
        )

        self.car_combo.addItem(
            "No eligible unassigned cars",
            None
        )

        self.car_combo.setCurrentIndex(
            0
        )

        self.car_combo.blockSignals(
            False
        )

    # ==========================================================
    # SPOT CHANGED
    # ==========================================================

    def spot_changed(self):
        """
        Reload the car list whenever the destination
        spot changes.

        This ensures the car list always reflects
        the restrictions of the selected spot.
        """

        spot_id = (
            self.spot_combo.currentData()
        )

        self.load_cars_for_spot(
            spot_id
        )

    # ==========================================================
    # CLEAR CAR INFORMATION
    # ==========================================================

    def clear_car_information(self):
        """
        Clear the car information display.
        """

        self.reporting_mark_label.setText(
            "-"
        )

        self.car_type_label.setText(
            "-"
        )

        self.length_label.setText(
            "-"
        )

        self.owner_label.setText(
            "-"
        )

        self.status_label.setText(
            "-"
        )

        self.location_label.setText(
            "-"
        )

    # ==========================================================
    # UPDATE CAR INFORMATION
    # ==========================================================

    def update_car_information(self):
        """
        Display information about the selected car.
        """

        car_id = (
            self.car_combo.currentData()
        )

        if car_id is None:

            self.clear_car_information()

            #
            # Only disable the button if there is
            # no actual car selected.
            #

            self.assign_button.setEnabled(
                False
            )

            return

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id
            )

            if car is None:

                self.clear_car_information()

                self.assign_button.setEnabled(
                    False
                )

                return

            self.reporting_mark_label.setText(
                (
                    f"{car.reporting_mark} "
                    f"{car.number}"
                )
            )

            self.car_type_label.setText(
                car.car_type or "Unknown"
            )

            self.length_label.setText(
                (
                    f"{car.length} ft"
                    if car.length is not None
                    else "Unknown"
                )
            )

            self.owner_label.setText(
                car.owner or "Unknown"
            )

            self.status_label.setText(
                car.status or "Unknown"
            )

            self.location_label.setText(
                car.location or "Unassigned"
            )

        #
        # A car is selected, so allow assignment.
        #

        self.assign_button.setEnabled(
            True
        )

    # ==========================================================
    # LOAD INDUSTRIES
    # ==========================================================

    def load_industries(
        self,
        selected_industry_id=None,
    ):
        """
        Load industries into the destination combo.
        """

        self.industry_combo.blockSignals(
            True
        )

        self.industry_combo.clear()

        with SessionLocal() as session:

            industries = (
                session.query(Industry)
                .order_by(
                    Industry.name
                )
                .all()
            )

            for industry in industries:

                self.industry_combo.addItem(
                    industry.name,
                    industry.id
                )

        if selected_industry_id is not None:

            index = (
                self.industry_combo.findData(
                    selected_industry_id
                )
            )

            if index >= 0:

                self.industry_combo.setCurrentIndex(
                    index
                )

        self.industry_combo.blockSignals(
            False
        )

    # ==========================================================
    # LOAD TRACKS
    # ==========================================================

    def load_tracks(self):
        """
        Load tracks belonging to the selected industry.
        """

        self.track_combo.blockSignals(
            True
        )

        self.track_combo.clear()

        self.spot_combo.blockSignals(
            True
        )

        self.spot_combo.clear()

        self.spot_combo.blockSignals(
            False
        )

        #
        # No longer have a valid destination spot.
        #

        self.car_combo.clear()

        self.clear_car_information()

        self.assign_button.setEnabled(
            False
        )

        industry_id = (
            self.industry_combo.currentData()
        )

        if industry_id is None:

            self.track_combo.addItem(
                "No tracks available",
                None,
            )

            self.track_combo.blockSignals(
                False
            )

            return

        with SessionLocal() as session:

            tracks = (
                session.query(IndustryTrack)
                .filter(
                    IndustryTrack.industry_id
                    == industry_id
                )
                .order_by(
                    IndustryTrack.name
                )
                .all()
            )

            for track in tracks:

                self.track_combo.addItem(
                    track.name,
                    track.id
                )

        if not self.track_combo.count():

            self.track_combo.addItem(
                "No tracks available",
                None,
            )

        self.track_combo.blockSignals(
            False
        )

        self.load_spots()

    # ==========================================================
    # LOAD AVAILABLE SPOTS
    # ==========================================================

    def load_spots(self):
        """
        Load only unoccupied spots belonging to
        the selected track.
        """

        self.spot_combo.blockSignals(
            True
        )

        self.spot_combo.clear()

        #
        # Destination changed, so clear the current
        # car list until a spot is selected.
        #

        self.car_combo.blockSignals(
            True
        )

        self.car_combo.clear()

        self.car_combo.blockSignals(
            False
        )

        self.clear_car_information()

        self.assign_button.setEnabled(
            False
        )

        track_id = (
            self.track_combo.currentData()
        )

        if track_id is None:

            self.spot_combo.addItem(
                "No available spots",
                None,
            )

            self.spot_combo.blockSignals(
                False
            )

            self.load_cars_for_spot(
                None
            )

            return

        with SessionLocal() as session:

            occupied_spot_ids = {
                row[0]
                for row in (
                    session.query(
                        Car.spot_id
                    )
                    .filter(
                        Car.spot_id.isnot(None)
                    )
                    .all()
                )
            }

            spots = (
                session.query(Spot)
                .filter(
                    Spot.track_id == track_id
                )
                .order_by(
                    Spot.spot_number
                )
                .all()
            )

            for spot in spots:

                if spot.id in occupied_spot_ids:

                    continue

                self.spot_combo.addItem(
                    f"Spot {spot.spot_number}",
                    spot.id
                )

        self.spot_combo.blockSignals(
            False
        )

        #
        # Select the first available spot and load
        # cars that satisfy its restrictions.
        #

        if self.spot_combo.count():

            self.spot_combo.setCurrentIndex(
                0
            )

            self.spot_changed()

        else:

            self.spot_combo.addItem(
                "No available spots",
                None,
            )

            self.load_cars_for_spot(
                None
            )

    # ==========================================================
    # LOAD FIXED DESTINATION
    # ==========================================================

    def load_fixed_destination(self):
        """
        Display the destination when this dialog
        was opened for a specific spot.

        The fixed spot is also used to filter the
        car list.
        """

        with SessionLocal() as session:

            spot = session.get(
                Spot,
                self.fixed_spot_id
            )

            if spot is None:

                self.destination_label.setText(
                    "Spot not found"
                )

                self.clear_car_information()

                self.assign_button.setEnabled(
                    False
                )

                return

            track = session.get(
                IndustryTrack,
                spot.track_id
            )

            if track is None:

                self.destination_label.setText(
                    "Track not found"
                )

                self.clear_car_information()

                self.assign_button.setEnabled(
                    False
                )

                return

            industry = session.get(
                Industry,
                track.industry_id
            )

            if industry is None:

                self.destination_label.setText(
                    "Industry not found"
                )

                self.clear_car_information()

                self.assign_button.setEnabled(
                    False
                )

                return

            #
            # Show destination.
            #

            self.destination_label.setText(
                (
                    f"{industry.name} - "
                    f"{track.name} - "
                    f"Spot {spot.spot_number}"
                )
            )

        #
        # Now that the fixed destination is known,
        # load only eligible cars.
        #

        self.load_cars_for_spot(
            self.fixed_spot_id
        )

    # ==========================================================
    # ASSIGN CAR
    # ==========================================================

    def assign_car(self):
        """
        Assign the selected car to the selected spot.

        The final validation is performed by
        CarLocationService immediately before
        the database transaction.
        """

        car_id = (
            self.car_combo.currentData()
        )

        if car_id is None:

            QMessageBox.warning(
                self,
                "No Car",
                "Please select an eligible car."
            )

            return

        #
        # Determine destination.
        #

        if self.fixed_spot_id is not None:

            spot_id = self.fixed_spot_id

        else:

            spot_id = (
                self.spot_combo.currentData()
            )

        if spot_id is None:

            QMessageBox.warning(
                self,
                "No Spot",
                (
                    "Please select an available "
                    "destination spot."
                )
            )

            return

        #
        # Final safety check.
        #
        # This verifies the car has not been assigned
        # somewhere else since the dialog was opened.
        #

        with SessionLocal() as session:

            car = session.get(
                Car,
                car_id
            )

            if car is None:

                QMessageBox.warning(
                    self,
                    "Car Not Found",
                    "The selected car could not be found."
                )

                return

            if (
                car.spot_id is not None
                or car.track_id is not None
                or car.industry_id is not None
            ):

                QMessageBox.warning(
                    self,
                    "Car Already Assigned",
                    (
                        "This car is already assigned "
                        "to a location.\n\n"
                        "Use Move Car to change its "
                        "current location."
                    )
                )

                #
                # Refresh the eligible list.
                #

                self.load_cars_for_spot(
                    spot_id
                )

                return

        #
        # Perform the assignment through the
        # central movement service.
        #

        result, message = (
            CarLocationService.assign_car_to_spot_with_message(
                car_id,
                spot_id
            )
        )

        #
        # Successful assignment.
        #

        if result:

            self.selected_spot_id = spot_id

            self.accept()

            return

        #
        # Failed assignment.
        #

        QMessageBox.warning(
            self,
            "Assignment Failed",
            (
                message
                if message
                else "Unable to assign car."
            )
        )

        #
        # Refresh the list in case the reason was
        # a changed car or spot restriction.
        #

        self.load_cars_for_spot(
            spot_id
        )
