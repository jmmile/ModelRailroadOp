
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)

from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot
from modelrailroadops.services.car_service import CarService


class AddCarDialog(QDialog):
    """
    Dialog used to add or edit a freight car.
    """

    def __init__(
        self,
        parent=None,
        car=None
    ):

        super().__init__(parent)

        self.car = car

        self.setWindowTitle(
            "Add Freight Car"
        )

        self.resize(
            450,
            400
        )

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.reporting_mark = QLineEdit()

        self.number = QLineEdit()

        self.owner = QLineEdit()

        self.car_type = QComboBox()

        #
        # Keep the exact car-type identifiers.
        #
        # Only the presentation order is sorted.
        # No names are normalized or changed.
        #

        car_types = [
            "Boxcar",
            "Boxcar - High Cube",
            "Cattle Car",
            "Flatcar",
            "Flatcar - Bulkhead",
            "Flatcar - Centerbeam",
            "Flatcar - Trailer",
            "Flatcar - Center Depressed",
            "Tank Car (hazardous)",
            "Tank Car (general service)",
            "Tank Car (specialty)",    
            "Autorack",
            "Gondola",
            "Hopper Car (cylindrical)",
            "Hopper Car (covered)",
            "Hopper Car (open)",
            "Hopper Car (grain)",
            "Hopper Car (wood chips)",
            "Hopper Car (ore)",
            "Hopper Car (specialty)",
            "Refrigerator Car",
            "Spine Car",
            "Well Car",
            "Caboose",
            "Maintenance of Way (MoW) Car",
            "Maintenance of Way (MoW) Flatcar",
            "Maintenance of Way (MoW) Gondola",
            "Maintenance of Way (MoW) Hopper",
            "Maintenance of Way (MoW) Tank Car",
            "Maintenance of Way (MoW) Boxcar",
            "Maintenance of Way (MoW) Crane Car",
            "Passenger-Coach",
            "Passenger-Dome",
            "Passenger-Observation",
            "Passenger-Sleeper",
            "Passenger-Baggage",
            "Passenger-Dining",
        ]

        car_types.sort(
            key=str.casefold
        )

        self.car_type.addItems(
            car_types
        )

        self.length = QLineEdit()

        self.length.setPlaceholderText(
            "Length in feet"
        )

        self.status = QComboBox()

        self.status.addItems([
            "Available",
            "Loaded",
            "Empty",
            "In Shop",
            "Interchange Track",
        ])

        #
        # Operating location
        #

        self.industry = QComboBox()

        self.track = QComboBox()

        self.spot = QComboBox()

        self.industry.addItem(
            "Unassigned",
            None
        )

        self.track.addItem(
            "Unassigned",
            None
        )

        self.spot.addItem(
            "Unassigned",
            None
        )

        #
        # Form fields
        #

        form.addRow(
            "Reporting Mark",
            self.reporting_mark
        )

        form.addRow(
            "Number",
            self.number
        )

        form.addRow(
            "Owner",
            self.owner
        )

        form.addRow(
            "Car Type",
            self.car_type
        )

        form.addRow(
            "Length (ft)",
            self.length
        )

        form.addRow(
            "Status",
            self.status
        )

        form.addRow(
            "Industry",
            self.industry
        )

        form.addRow(
            "Track",
            self.track
        )

        form.addRow(
            "Spot",
            self.spot
        )

        layout.addLayout(
            form
        )

        #
        # Buttons
        #

        buttons = QHBoxLayout()

        self.save_button = QPushButton(
            "Save"
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )

        buttons.addStretch()

        buttons.addWidget(
            self.save_button
        )

        buttons.addWidget(
            self.cancel_button
        )

        layout.addLayout(
            buttons
        )

        #
        # Load industries
        #

        self.load_industries()

        #
        # Signals
        #

        self.industry.currentIndexChanged.connect(
            self.industry_changed
        )

        self.track.currentIndexChanged.connect(
            self.track_changed
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        self.save_button.clicked.connect(
            self.save
        )

        #
        # Populate edit fields
        #

        if self.car:

            self.reporting_mark.setText(
                self.car.reporting_mark
            )

            self.number.setText(
                self.car.number
            )

            self.owner.setText(
                self.car.owner
            )

            self.car_type.setCurrentText(
                self.car.car_type
            )

            if self.car.length is not None:

                self.length.setText(
                    str(self.car.length)
                )

            self.status.setCurrentText(
                self.car.status
            )

            self.setWindowTitle(
                "Edit Freight Car"
            )

            #
            # Restore existing location
            #

            if self.car.industry_id:

                self.select_industry(
                    self.car.industry_id
                )

    #
    # Industry loading
    #

    def load_industries(self):

        current_industry_id = None

        if self.industry.currentIndex() >= 0:

            current_industry_id = (
                self.industry.currentData()
            )

        self.industry.blockSignals(True)

        self.industry.clear()

        self.industry.addItem(
            "Unassigned",
            None
        )

        with SessionLocal() as session:

            industries = (
                session.execute(
                    select(Industry)
                    .order_by(
                        Industry.name
                    )
                )
                .scalars()
                .all()
            )

            for industry in industries:

                self.industry.addItem(
                    industry.name,
                    industry.id
                )

        if current_industry_id is not None:

            index = self.industry.findData(
                current_industry_id
            )

            if index >= 0:

                self.industry.setCurrentIndex(
                    index
                )

        self.industry.blockSignals(False)

        self.load_tracks()

    #
    # Industry changed
    #

    def industry_changed(
        self,
        index
    ):

        self.load_tracks()

    #
    # Load tracks
    #

    def load_tracks(
        self,
        selected_track_id=None
    ):

        industry_id = (
            self.industry.currentData()
        )

        self.track.blockSignals(True)

        self.track.clear()

        self.track.addItem(
            "Unassigned",
            None
        )

        if industry_id is not None:

            with SessionLocal() as session:

                tracks = (
                    session.execute(
                        select(IndustryTrack)
                        .where(
                            IndustryTrack.industry_id
                            == industry_id
                        )
                        .order_by(
                            IndustryTrack.name
                        )
                    )
                    .scalars()
                    .all()
                )

                for track in tracks:

                    self.track.addItem(
                        track.name,
                        track.id
                    )

        if selected_track_id is not None:

            index = self.track.findData(
                selected_track_id
            )

            if index >= 0:

                self.track.setCurrentIndex(
                    index
                )

        self.track.blockSignals(False)

        self.load_spots()

    #
    # Track changed
    #

    def track_changed(
        self,
        index
    ):

        self.load_spots()

    #
    # Load spots
    #

    def load_spots(
        self,
        selected_spot_id=None
    ):

        track_id = (
            self.track.currentData()
        )

        self.spot.blockSignals(True)

        self.spot.clear()

        self.spot.addItem(
            "Unassigned",
            None
        )

        if track_id is not None:

            with SessionLocal() as session:

                spots = (
                    session.execute(
                        select(Spot)
                        .where(
                            Spot.track_id
                            == track_id
                        )
                        .order_by(
                            Spot.spot_number
                        )
                    )
                    .scalars()
                    .all()
                )

                for spot in spots:

                    occupied = (
                        spot.car is not None
                    )

                    if occupied:

                        label = (
                            f"Spot {spot.spot_number}"
                            f" - Occupied"
                        )

                    else:

                        label = (
                            f"Spot {spot.spot_number}"
                        )

                    if spot.name:

                        label += (
                            f" - {spot.name}"
                        )

                    self.spot.addItem(
                        label,
                        spot.id
                    )

        if selected_spot_id is not None:

            index = self.spot.findData(
                selected_spot_id
            )

            if index >= 0:

                self.spot.setCurrentIndex(
                    index
                )

        self.spot.blockSignals(False)

    #
    # Select an existing industry
    #

    def select_industry(
        self,
        industry_id
    ):

        index = self.industry.findData(
            industry_id
        )

        if index < 0:

            return

        self.industry.blockSignals(True)

        self.industry.setCurrentIndex(
            index
        )

        self.industry.blockSignals(False)

        self.load_tracks(
            selected_track_id=(
                self.car.track_id
                if self.car
                else None
            )
        )

        self.load_spots(
            selected_spot_id=(
                self.car.spot_id
                if self.car
                else None
            )
        )

    #
    # Save
    #

    def save(self):

        reporting_mark = (
            self.reporting_mark.text()
            .strip()
            .upper()
        )

        number = (
            self.number.text()
            .strip()
        )

        owner = (
            self.owner.text()
            .strip()
        )

        if not reporting_mark:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a reporting mark."
            )

            return

        if not number:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a car number."
            )

            return

        length_text = (
            self.length.text()
            .strip()
        )

        length = None

        if length_text:

            try:

                length = int(
                    length_text
                )

            except ValueError:

                QMessageBox.warning(
                    self,
                    "Invalid Length",
                    "Car length must be a whole number."
                )

                return

        status = (
            self.status.currentText()
        )

        industry_id = (
            self.industry.currentData()
        )

        track_id = (
            self.track.currentData()
        )

        spot_id = (
            self.spot.currentData()
        )

        #
        # A spot can only be selected when
        # a track and industry are selected.
        #

        if spot_id is not None:

            if track_id is None:

                QMessageBox.warning(
                    self,
                    "Invalid Location",
                    "Please select a track."
                )

                return

            if industry_id is None:

                QMessageBox.warning(
                    self,
                    "Invalid Location",
                    "Please select an industry."
                )

                return

        #
        # Edit existing car
        #

        if self.car:

            updated_car = CarService.update(
                car_id=self.car.id,

                reporting_mark=reporting_mark,

                number=number,

                owner=owner,

                car_type=(
                    self.car_type.currentText()
                ),

                length=length,

                status=status,

                location=self.car.location,
            )

            if updated_car is None:

                QMessageBox.warning(
                    self,
                    "Error",
                    "The freight car could not be updated."
                )

                return

            try:

                if spot_id is not None:

                    CarService.assign_to_spot(
                        self.car.id,
                        spot_id
                    )

                else:

                    CarService.clear_spot_assignment(
                        self.car.id
                    )

            except ValueError as ex:

                QMessageBox.warning(
                    self,
                    "Location Error",
                    str(ex)
                )

                return

        #
        # Add new car
        #

        else:

            car = CarService.add(
                reporting_mark=reporting_mark,

                number=number,

                owner=owner,

                car_type=(
                    self.car_type.currentText()
                ),

                length=length,

                status=status,

                location="Unassigned",
            )

            if car is None:

                QMessageBox.warning(
                    self,
                    "Duplicate Car",
                    (
                        "A freight car with the same "
                        "reporting mark and number "
                        "already exists."
                    )
                )

                return

            #
            # Assign the new car to the
            # selected spot.
            #

            if spot_id is not None:

                try:

                    CarService.assign_to_spot(
                        car.id,
                        spot_id
                    )

                except ValueError as ex:

                    #
                    # Remove the newly-created car
                    # if its requested location
                    # cannot be assigned.
                    #

                    CarService.delete(
                        car.id
                    )

                    QMessageBox.warning(
                        self,
                        "Location Error",
                        str(ex)
                    )

                    return

        self.accept()
