
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


class MoveCarDialog(QDialog):
    """
    Dialog used to move an existing car to another spot.

    The destination is selected by:

        Industry
            -> Track
                -> Spot

    Only unoccupied spots are displayed.

    All movement validation is performed by
    CarLocationService.
    """

    def __init__(
        self,
        car_id,
        parent=None,
    ):

        super().__init__(parent)

        self.car_id = car_id

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
        # Destination form
        #

        form = QFormLayout()

        self.industry_combo = QComboBox()

        self.track_combo = QComboBox()

        self.spot_combo = QComboBox()

        form.addRow(
            "Destination Industry",
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

        move_button = QPushButton(
            "Move"
        )

        cancel_button = QPushButton(
            "Cancel"
        )

        buttons.addStretch()

        buttons.addWidget(
            move_button
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

        move_button.clicked.connect(
            self.move_car
        )

        cancel_button.clicked.connect(
            self.reject
        )

        #
        # Load initial data
        #

        self.load_car()

        self.load_industries()

        self.industry_combo.currentIndexChanged.connect(
            self.load_tracks
        )

        self.track_combo.currentIndexChanged.connect(
            self.load_spots
        )

        self.load_tracks()

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

                return

            self.car_label.setText(
                (
                    f"Move: "
                    f"{car.reporting_mark} "
                    f"{car.number}"
                )
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
        """

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
        """

        self.spot_combo.clear()

        track_id = (
            self.track_combo.currentData()
        )

        if track_id is None:

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
                    f"Spot {spot.spot_number}",
                    spot.id
                )

        #
        # Disable Move when there are no
        # available destination spots.
        #

       
    #
    # Move car
    #

    def move_car(self):
        """
        Move the car to the selected destination.

        CarLocationService performs the final
        validation immediately before changing
        the database.
        """

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
        # Perform the move using the detailed
        # service method so that validation
        # errors can be displayed.
        #

        result, message = (
            CarLocationService.assign_car_to_spot_with_message(
                self.car_id,
                spot_id
            )
        )

        #
        # Successful move
        #

        if result:

            self.accept()

            return

        #
        # Failed move
        #

        QMessageBox.warning(
            self,
            "Move Failed",
            (
                message
                if message
                else "Unable to move car."
            )
        )
