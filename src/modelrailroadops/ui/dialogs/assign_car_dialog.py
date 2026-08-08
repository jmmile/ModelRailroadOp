#```python
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QLabel,
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
    Dialog used to assign or move a car to a spot.

    ASSIGN mode:
        Only unassigned cars are displayed.

    MOVE mode:
        The specified car is displayed and can be moved
        to another destination.

    Car dropdown displays:

        Reporting Mark Number — Car Type

    Example:

        UP 12345 — Boxcar
    """

    def __init__(
        self,
        spot_id=None,
        car_id=None,
        industry_id=None,
        parent=None,
    ):

        super().__init__(parent)

        self.fixed_spot_id = spot_id
        self.fixed_car_id = car_id
        self.fixed_industry_id = industry_id

        self.selected_spot_id = None

        #
        # Determine operating mode
        #

        if self.fixed_car_id:

            self.mode = "MOVE"

        else:

            self.mode = "ASSIGN"

        #
        # Window
        #

        self.setWindowTitle(
            "Move Car"
            if self.mode == "MOVE"
            else "Assign Car"
        )

        self.resize(
            550,
            420
        )

        #
        # Main layout
        #

        layout = QVBoxLayout(self)

        #
        # Form
        #

        form = QFormLayout()

        #
        # Car
        #

        self.car_combo = QComboBox()

        if self.mode == "ASSIGN":

            form.addRow(
                "Car",
                self.car_combo
            )

        #
        # Destination
        #

        self.industry_combo = QComboBox()
        self.track_combo = QComboBox()
        self.spot_combo = QComboBox()

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

            self.destination_label = QLabel()

            form.addRow(
                "Destination",
                self.destination_label
            )

        layout.addLayout(form)

        #
        # Car information
        #

        info_group = QGroupBox(
            "Car Information"
        )

        info_form = QFormLayout()

        self.reporting_mark_label = QLabel("-")
        self.car_type_label = QLabel("-")
        self.length_label = QLabel("-")
        self.location_label = QLabel("-")

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
            "Move"
            if self.mode == "MOVE"
            else "Assign"
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

        layout.addLayout(buttons)

        #
        # Signals
        #

        self.assign_button.clicked.connect(
            self.assign
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        #
        # Load data
        #

        if self.mode == "ASSIGN":

            self.load_cars()

            self.car_combo.currentIndexChanged.connect(
                self.update_car_information
            )

        else:

            self.update_car_information()

        #
        # Fixed destination
        #

        if self.fixed_spot_id:

            self.load_destination_name()

        else:

            self.load_industries(
                self.fixed_industry_id
            )

            self.industry_combo.currentIndexChanged.connect(
                self.load_tracks
            )

            self.track_combo.currentIndexChanged.connect(
                self.load_spots
            )

            self.load_tracks()

    #
    # Load cars
    #

    def load_cars(self):
        """
        Load only cars that are not currently assigned
        to a spot.

        This prevents an already assigned car from being
        selected for a second assignment.
        """

        self.car_combo.clear()

        with SessionLocal() as session:

            #
            # A car is considered assigned if it has
            # either a spot_id or a track_id.
            #
            # Cars without either location are available.
            #

            cars = (
                session.query(Car)
                .filter(
                    Car.spot_id.is_(None),
                    Car.track_id.is_(None),
                )
                .order_by(
                    Car.reporting_mark,
                    Car.number
                )
                .all()
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

        #
        # Select first available car
        #

        if self.car_combo.count():

            self.car_combo.setCurrentIndex(0)

            self.update_car_information()

        else:

            self.reporting_mark_label.setText(
                "-"
            )

            self.car_type_label.setText(
                "-"
            )

            self.length_label.setText(
                "-"
            )

            self.location_label.setText(
                "-"
            )

            self.assign_button.setEnabled(
                False
            )

    #
    # Update selected car information
    #

    def update_car_information(self):

        with SessionLocal() as session:

            car_id = (
                self.fixed_car_id
                if self.mode == "MOVE"
                else self.car_combo.currentData()
            )

            if car_id is None:

                return

            car = session.get(
                Car,
                car_id
            )

            if not car:

                return

            self.reporting_mark_label.setText(
                f"{car.reporting_mark} {car.number}"
            )

            self.car_type_label.setText(
                car.car_type or "Unknown"
            )

            self.length_label.setText(
                f"{car.length} ft"
                if car.length
                else "Unknown"
            )

            self.location_label.setText(
                car.location or "Unassigned"
            )

    #
    # Load industries
    #

    def load_industries(
        self,
        selected_industry_id=None
    ):

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

        if selected_industry_id:

            index = self.industry_combo.findData(
                selected_industry_id
            )

            if index >= 0:

                self.industry_combo.setCurrentIndex(
                    index
                )

    #
    # Load tracks
    #

    def load_tracks(self):

        self.track_combo.clear()

        self.spot_combo.clear()

        industry_id = (
            self.industry_combo.currentData()
        )

        if industry_id is None:

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

        self.load_spots()

    #
    # Load available spots
    #

    def load_spots(self):

        self.spot_combo.clear()

        track_id = self.track_combo.currentData()

        if track_id is None:

            return

        with SessionLocal() as session:

            spots = (
                session.query(Spot)
                .filter(
                    Spot.track_id == track_id,
                    Spot.car == None
                )
                .order_by(
                    Spot.spot_number
                )
                .all()
            )

            for spot in spots:

                self.spot_combo.addItem(
                    f"Spot {spot.spot_number}",
                    spot.id
                )

    #
    # Load fixed destination
    #

    def load_destination_name(self):

        with SessionLocal() as session:

            spot = session.get(
                Spot,
                self.fixed_spot_id
            )

            if spot:

                track = session.get(
                    IndustryTrack,
                    spot.track_id
                )

                if track:

                    industry = session.get(
                        Industry,
                        track.industry_id
                    )

                    if industry:

                        self.destination_label.setText(
                            f"{industry.name} - "
                            f"{track.name} - "
                            f"Spot {spot.spot_number}"
                        )

    #
    # Assign / move car
    #

    def assign(self):

        car_id = (
            self.fixed_car_id
            if self.mode == "MOVE"
            else self.car_combo.currentData()
        )

        spot_id = (
            self.fixed_spot_id
            if self.fixed_spot_id
            else self.spot_combo.currentData()
        )

        if car_id is None or spot_id is None:

            QMessageBox.warning(
                self,
                "Missing Selection",
                "Select a car and destination."
            )

            return

        #
        # Final safety check.
        #
        # Even though assigned cars are removed from
        # the Assign dropdown, check again immediately
        # before assigning.
        #

        if self.mode == "ASSIGN":

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
                ):

                    QMessageBox.warning(
                        self,
                        "Car Already Assigned",
                        (
                            "This car is already assigned "
                            "to a location.\n\n"
                            "Move the existing assignment "
                            "instead of assigning the car again."
                        )
                    )

                    return

        #
        # Assign car
        #

        result = CarLocationService.assign_car_to_spot(
            car_id,
            spot_id
        )

        if result:

            self.selected_spot_id = spot_id

            self.accept()

        else:

            QMessageBox.warning(
                self,
                "Failed",
                "Unable to complete operation."
            )
