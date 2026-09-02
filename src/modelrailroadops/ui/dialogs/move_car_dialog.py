from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.car import Car

from modelrailroadops.services.car_location_service import (
    CarLocationService,
)

from modelrailroadops.services.waybill_service import (
    WaybillService,
)


class MoveCarDialog(QDialog):
    """
    Dialog used to move an existing car to another spot.

    If the car has one active waybill, the destination is controlled
    by the waybill:

        Active Waybill
            -> Destination Industry
                -> Destination Track
                    -> Destination Spot

    The user cannot select an unrelated destination for a car
    that has an active waybill.

    If the car has no active waybill, manual movement is allowed:

        Industry
            -> Track
                -> Spot

    Only unoccupied spots are displayed.

    All physical movement validation is performed by
    CarLocationService.

    When a car with an active waybill is successfully moved to its
    waybill destination, the waybill is completed through
    WaybillService.
    """

    def __init__(
        self,
        car_id,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.car_id = car_id

        self.active_waybill = None

        self.move_button = None

        self.setWindowTitle(
            "Move Car"
        )

        self.resize(
            450,
            300
        )

        #
        # Main layout
        #

        layout = QVBoxLayout(
            self
        )

        #
        # Car information
        #

        self.car_label = QLabel()

        self.car_label.setText(
            "Car: Unknown"
        )

        layout.addWidget(
            self.car_label
        )

        #
        # Waybill information
        #

        self.waybill_label = QLabel()

        self.waybill_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.waybill_label
        )

        #
        # Destination form
        #

        form = QFormLayout()

        self.industry_combo = QComboBox()

        self.track_combo = QComboBox()

        self.spot_combo = QComboBox()

        form.addRow(
            "Destination Location",
            self.industry_combo
        )

        form.addRow(
            "Destination Track",
            self.track_combo
        )

        form.addRow(
            "Destination Spot",
            self.spot_combo
        )

        layout.addLayout(
            form
        )

        #
        # Buttons
        #

        buttons = QHBoxLayout()

        self.move_button = QPushButton(
            "Move"
        )

        cancel_button = QPushButton(
            "Cancel"
        )

        buttons.addStretch()

        buttons.addWidget(
            self.move_button
        )

        buttons.addWidget(
            cancel_button
        )

        layout.addLayout(
            buttons
        )

        #
        # Signals
        #

        self.move_button.clicked.connect(
            self.move_car
        )

        cancel_button.clicked.connect(
            self.reject
        )

        self.industry_combo.currentIndexChanged.connect(
            self.load_tracks
        )

        self.track_combo.currentIndexChanged.connect(
            self.load_spots
        )

        #
        # Load initial data
        #

        self.load_car()

        self.load_active_waybill()

        #
        # Configure the dialog based on whether
        # the car has an active waybill.
        #

        if self.active_waybill is not None:

            self.configure_waybill_destination()

        else:

            self.configure_manual_destination()

    #
    # Load car
    #

    def load_car(self):
        """
        Load the car being moved and display
        its reporting mark and number.
        """

        with SessionLocal() as session:

            car = session.get(
                Car,
                self.car_id
            )

            if car is None:

                self.car_label.setText(
                    "Car: Not Found"
                )

                self.move_button.setEnabled(
                    False
                )

                return

            self.car_label.setText(
                (
                    f"Move: "
                    f"{car.reporting_mark} "
                    f"{car.number}"
                )
            )

    #
    # Load active waybill
    #

    def load_active_waybill(self):
        """
        Load the car's active waybill.

        WaybillService returns a list. Normally there should
        be zero or one active waybill because WaybillService
        prevents multiple active or in-progress waybills
        from being created for the same car.

        If multiple active waybills are found, movement is
        blocked rather than choosing one arbitrarily.
        """

        try:

            waybills = (
                WaybillService.get_active_for_car(
                    self.car_id
                )
            )

        except Exception as ex:

            self.active_waybill = None

            self.waybill_label.setText(
                "Unable to determine the car's active waybill."
            )

            self.move_button.setEnabled(
                False
            )

            QMessageBox.warning(
                self,
                "Waybill Lookup Failed",
                (
                    "The car's active waybill could not "
                    "be determined.\n\n"
                    f"{ex}"
                )
            )

            return

        #
        # No active waybill.
        #

        if not waybills:

            self.active_waybill = None

            return

        #
        # More than one active waybill indicates
        # inconsistent database data.
        #

        if len(
            waybills
        ) > 1:

            self.active_waybill = None

            self.waybill_label.setText(
                (
                    "Multiple active waybills were found "
                    "for this car. Movement is disabled "
                    "until the waybills are corrected."
                )
            )

            self.move_button.setEnabled(
                False
            )

            QMessageBox.warning(
                self,
                "Multiple Active Waybills",
                (
                    "This car has more than one active "
                    "waybill.\n\n"
                    "The car cannot be moved automatically "
                    "until the conflicting waybills are "
                    "corrected."
                )
            )

            return

        #
        # Exactly one active waybill.
        #

        self.active_waybill = (
            waybills[0]
        )

    #
    # Configure manual destination
    #

    def configure_manual_destination(self):
        """
        Configure the dialog for a car without
        an active waybill.

        Manual Industry -> Track -> Spot selection
        remains available.
        """

        self.waybill_label.setText(
            (
                "No active waybill. "
                "Manual destination selection is allowed."
            )
        )

        self.move_button.setText(
            "Move"
        )

        self.load_industries()

        self.load_tracks()

    #
    # Configure waybill destination
    #

    def configure_waybill_destination(self):
        """
        Configure the dialog so the destination is taken
        directly from the active waybill.

        The destination controls are populated from the
        waybill and disabled so the user cannot redirect
        the car to another location.
        """

        waybill = self.active_waybill

        destination_industry = (
            waybill.destination_industry
        )

        destination_track = (
            waybill.destination_track
        )

        destination_spot = (
            waybill.destination_spot
        )

        destination_location = getattr(
            waybill,
            "destination_operating_location",
            None,
        )

        destination_operating_track = getattr(
            waybill,
            "destination_operating_track",
            None,
        )

        # Yard, staging, and interchange destinations use a general
        # LocationTrack and intentionally have no Spot.
        if destination_spot is None:

            if destination_location is None or destination_operating_track is None:
                self.waybill_label.setText(
                    f"Active Waybill #{waybill.id} has no complete destination."
                )
                self.move_button.setEnabled(False)
                return

            self.waybill_label.setText(
                (
                    f"Active Waybill #{waybill.id} — Destination: "
                    f"{destination_location.name} → "
                    f"{destination_operating_track.name}"
                )
            )

            for combo in (
                self.industry_combo,
                self.track_combo,
                self.spot_combo,
            ):
                combo.blockSignals(True)
                combo.clear()

            self.industry_combo.addItem(
                destination_location.name,
                destination_location.id,
            )
            self.track_combo.addItem(
                destination_operating_track.name,
                destination_operating_track.id,
            )
            self.spot_combo.addItem("Not required", None)

            for combo in (
                self.industry_combo,
                self.track_combo,
                self.spot_combo,
            ):
                combo.blockSignals(False)
                combo.setEnabled(False)

            self.move_button.setText("Move to Waybill Destination")
            self.move_button.setEnabled(True)
            return

        if destination_industry is None:

            self.waybill_label.setText(
                (
                    f"Active Waybill #{waybill.id} "
                    "has no destination industry."
                )
            )

            self.move_button.setEnabled(
                False
            )

            return

        if destination_track is None:

            self.waybill_label.setText(
                (
                    f"Active Waybill #{waybill.id} "
                    "has no destination track."
                )
            )

            self.move_button.setEnabled(
                False
            )

            return

        if destination_spot is None:

            self.waybill_label.setText(
                (
                    f"Active Waybill #{waybill.id} "
                    "has no destination spot."
                )
            )

            self.move_button.setEnabled(
                False
            )

            return

        #
        # Display the active waybill and destination.
        #

        self.waybill_label.setText(
            (
                f"Active Waybill #{waybill.id} — "
                f"Destination: "
                f"{destination_industry.name} → "
                f"{destination_track.name} → "
                f"Spot {destination_spot.spot_number}"
            )
        )

        #
        # Populate the destination controls directly
        # from the waybill.
        #

        self.industry_combo.blockSignals(
            True
        )

        self.track_combo.blockSignals(
            True
        )

        self.spot_combo.blockSignals(
            True
        )

        self.industry_combo.clear()

        self.track_combo.clear()

        self.spot_combo.clear()

        self.industry_combo.addItem(
            destination_industry.name,
            destination_industry.id
        )

        self.track_combo.addItem(
            destination_track.name,
            destination_track.id
        )

        self.spot_combo.addItem(
            (
                f"Spot "
                f"{destination_spot.spot_number}"
            ),
            destination_spot.id
        )

        self.industry_combo.blockSignals(
            False
        )

        self.track_combo.blockSignals(
            False
        )

        self.spot_combo.blockSignals(
            False
        )

        #
        # Lock all destination controls.
        #

        self.industry_combo.setEnabled(
            False
        )

        self.track_combo.setEnabled(
            False
        )

        self.spot_combo.setEnabled(
            False
        )

        #
        # Verify that the destination spot is
        # currently available.
        #

        if self.is_spot_occupied(
            destination_spot.id
        ):

            self.waybill_label.setText(
                (
                    f"Active Waybill #{waybill.id} — "
                    f"Destination: "
                    f"{destination_industry.name} → "
                    f"{destination_track.name} → "
                    f"Spot {destination_spot.spot_number}\n"
                    "Destination spot is currently occupied."
                )
            )

            self.move_button.setEnabled(
                False
            )

            return

        #
        # The waybill destination is available.
        #

        self.move_button.setText(
            "Move to Waybill Destination"
        )

        self.move_button.setEnabled(
            True
        )

    #
    # Load industries
    #

    def load_industries(self):
        """
        Load all industries into the destination
        industry combo box.
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

        self.industry_combo.blockSignals(
            False
        )

    #
    # Load tracks
    #

    def load_tracks(self):
        """
        Load tracks belonging to the selected
        industry.

        This method is used only for manual movement.
        """

        if self.active_waybill is not None:

            return

        self.track_combo.blockSignals(
            True
        )

        self.track_combo.clear()

        self.spot_combo.clear()

        industry_id = (
            self.industry_combo.currentData()
        )

        if industry_id is None:

            self.track_combo.blockSignals(
                False
            )

            self.update_move_button()

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

        self.track_combo.blockSignals(
            False
        )

        self.load_spots()

    #
    # Load available spots
    #

    def load_spots(self):
        """
        Load only unoccupied spots belonging to
        the selected track.

        This method is used only for manual movement.
        """

        if self.active_waybill is not None:

            return

        self.spot_combo.clear()

        track_id = (
            self.track_combo.currentData()
        )

        if track_id is None:

            self.update_move_button()

            return

        with SessionLocal() as session:

            #
            # Get IDs of all currently occupied spots.
            #

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

            #
            # Load spots belonging to the
            # selected track.
            #

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

                #
                # Do not offer occupied spots.
                #

                if spot.id in occupied_spot_ids:

                    continue

                self.spot_combo.addItem(
                    (
                        f"Spot "
                        f"{spot.spot_number}"
                    ),
                    spot.id
                )

        #
        # Disable Move when there are no
        # available destination spots.
        #

        self.update_move_button()

    #
    # Check spot occupancy
    #

    def is_spot_occupied(
        self,
        spot_id,
    ):
        """
        Check the database immediately to determine
        whether a spot currently contains a car.
        """

        if spot_id is None:

            return False

        with SessionLocal() as session:

            car = (
                session.query(Car)
                .filter(
                    Car.spot_id == spot_id
                )
                .first()
            )

            return car is not None

    #
    # Update Move button
    #

    def update_move_button(self):
        """
        Enable Move only when a valid destination spot
        is available.
        """

        if self.active_waybill is not None:

            return

        spot_id = (
            self.spot_combo.currentData()
        )

        self.move_button.setEnabled(
            spot_id is not None
        )

    #
    # Move car
    #

    def move_car(self):
        """
        Move the car to its destination.

        For a car with an active waybill, the destination
        is always taken from the waybill.

        For a car without an active waybill, the selected
        manual destination is used.

        A successful waybill-driven movement completes the
        waybill through WaybillService.
        """

        #
        # Determine the destination.
        #

        general_track_id = None

        if self.active_waybill is not None:

            waybill = self.active_waybill

            destination_spot = (
                waybill.destination_spot
            )

            if destination_spot is None:

                general_track_id = getattr(
                    waybill,
                    "destination_location_track_id",
                    None,
                )

                if general_track_id is None:
                    QMessageBox.warning(
                        self,
                        "Invalid Waybill",
                        f"Waybill #{waybill.id} has no complete destination.",
                    )
                    return

                spot_id = None

            else:

                spot_id = (
                    destination_spot.id
                )

            #
            # Recheck occupancy immediately before
            # changing the database.
            #

            if spot_id is not None and self.is_spot_occupied(spot_id):

                QMessageBox.warning(
                    self,
                    "Destination Occupied",
                    (
                        f"Waybill #{waybill.id} "
                        "requires Spot "
                        f"{destination_spot.spot_number}, "
                        "but that spot is currently occupied."
                    )
                )

                self.move_button.setEnabled(
                    False
                )

                return

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
        # Perform the physical move using the detailed
        # service method so validation errors are returned.
        #

        if general_track_id is not None:
            result, message = (
                CarLocationService.move_car_to_location_track_with_message(
                    self.car_id,
                    general_track_id,
                    self.active_waybill.operations_session_id,
                )
            )
        else:
            result, message = (
                CarLocationService.assign_car_to_spot_with_message(
                    self.car_id,
                    spot_id,
                    (
                        self.active_waybill.operations_session_id
                        if self.active_waybill is not None
                        else None
                    ),
                )
            )

        #
        # Failed physical move.
        #

        if not result:

            QMessageBox.warning(
                self,
                "Move Failed",
                (
                    message
                    if message
                    else "Unable to move car."
                )
            )

            return

        #
        # If this car has an active waybill, complete
        # that waybill now that the car has reached
        # its required destination.
        #

        if self.active_waybill is not None:

            success, completion_result = (
                WaybillService.complete(
                    self.active_waybill.id
                )
            )

            if not success:

                QMessageBox.warning(
                    self,
                    "Waybill Completion Failed",
                    (
                        "The car was moved successfully, "
                        "but the waybill could not be "
                        "completed.\n\n"
                        f"{completion_result}"
                    )
                )

                #
                # The physical movement succeeded, so
                # close the dialog rather than pretending
                # that the move itself failed.
                #

                self.accept()

                return

        #
        # Successful movement.
        #

        self.accept()
