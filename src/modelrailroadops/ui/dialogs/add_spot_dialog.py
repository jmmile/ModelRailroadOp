from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QPushButton,
    QHBoxLayout,
)


class AddSpotDialog(QDialog):
    """
    Dialog used for adding and editing
    track spots.

    The Allowed Car Type list intentionally uses
    the exact same car-type identifiers as the
    Car Roster. This is important because spot
    restrictions are compared directly against
    Car.car_type.
    """

    #
    # IMPORTANT:
    #
    # These values must remain synchronized with
    # AddCarDialog.car_types.
    #
    # Do not rename these values independently in
    # the Spot dialog. They are stored as exact
    # identifiers and compared against Car.car_type.
    #

    CAR_TYPES = [
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

    def __init__(
        self,
        spot=None,
        track=None,
        parent=None,
    ):

        super().__init__(parent)

        self.spot = spot
        self.track = track

        if self.spot:
            self.setWindowTitle(
                "Edit Spot"
            )
        else:
            self.setWindowTitle(
                "Add Spot"
            )

        self.resize(
            450,
            450,
        )

        layout = QVBoxLayout(
            self
        )

        form = QFormLayout()

        #
        # Spot Number
        #

        self.spot_number = QSpinBox()

        self.spot_number.setMinimum(
            1
        )

        self.spot_number.setMaximum(
            9999
        )

        #
        # Name
        #

        self.name = QLineEdit()

        #
        # Description
        #

        self.description = QLineEdit()

        #
        # Maximum Length
        #

        self.max_length = QSpinBox()

        self.max_length.setMinimum(
            0
        )

        self.max_length.setMaximum(
            999
        )

        self.max_length.setSpecialValueText(
            "No Limit"
        )

        #
        # Allowed Car Type
        #

        self.allowed_car_type = QComboBox()

        self.allowed_car_type.addItem(
            "Any Car Type",
            None,
        )

        #
        # Use the exact same identifiers
        # used by the Car Roster.
        #

        car_types = sorted(
            self.CAR_TYPES,
            key=str.casefold,
        )

        for car_type in car_types:

            self.allowed_car_type.addItem(
                car_type,
                car_type,
            )

        #
        # Allowed Owner
        #

        self.allowed_owner = QLineEdit()

        self.allowed_owner.setPlaceholderText(
            "Any owner"
        )

        #
        # Restrictions
        #

        self.hazardous_allowed = QCheckBox(
            "Hazardous cars allowed"
        )

        self.hazardous_allowed.setChecked(
            True
        )

        self.load_only = QCheckBox(
            "Loaded cars only"
        )

        self.empty_only = QCheckBox(
            "Empty cars only"
        )

        #
        # Notes
        #

        self.notes = QLineEdit()

        #
        # Form
        #

        form.addRow(
            "Spot Number",
            self.spot_number,
        )

        form.addRow(
            "Name",
            self.name,
        )

        form.addRow(
            "Description",
            self.description,
        )

        form.addRow(
            "Maximum Length (ft)",
            self.max_length,
        )

        form.addRow(
            "Allowed Car Type",
            self.allowed_car_type,
        )

        form.addRow(
            "Allowed Owner",
            self.allowed_owner,
        )

        form.addRow(
            "",
            self.hazardous_allowed,
        )

        form.addRow(
            "",
            self.load_only,
        )

        form.addRow(
            "",
            self.empty_only,
        )

        form.addRow(
            "Notes",
            self.notes,
        )

        layout.addLayout(
            form
        )

        #
        # Buttons
        #

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

        #
        # Signals
        #

        self.ok_button.clicked.connect(
            self.accept
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        #
        # Edit mode
        #

        if self.spot:

            self.load_spot()

    #
    # Load existing spot
    #

    def load_spot(self):
        """
        Populate fields from an existing spot.
        """

        self.spot_number.setValue(
            self.spot.spot_number
        )

        self.name.setText(
            self.spot.name or ""
        )

        self.description.setText(
            self.spot.description or ""
        )

        if self.spot.max_length is not None:

            self.max_length.setValue(
                self.spot.max_length
            )

        else:

            self.max_length.setValue(
                0
            )

        #
        # Restore the exact stored car type.
        #

        if self.spot.allowed_car_type:

            index = (
                self.allowed_car_type.findData(
                    self.spot.allowed_car_type
                )
            )

            if index >= 0:

                self.allowed_car_type.setCurrentIndex(
                    index
                )

        else:

            self.allowed_car_type.setCurrentIndex(
                0
            )

        self.allowed_owner.setText(
            self.spot.allowed_owner or ""
        )

        self.hazardous_allowed.setChecked(
            self.spot.hazardous_allowed
        )

        self.load_only.setChecked(
            self.spot.load_only
        )

        self.empty_only.setChecked(
            self.spot.empty_only
        )

        self.notes.setText(
            self.spot.notes or ""
        )

        #
        # Do not allow spot number changes
        # when editing an existing spot.
        #

        self.spot_number.setEnabled(
            False
        )

        self.ok_button.setText(
            "Save"
        )

    #
    # Get data
    #

    def get_data(self):
        """
        Return the values entered in the dialog.
        """

        max_length = (
            self.max_length.value()
        )

        if max_length == 0:

            max_length = None

        allowed_car_type = (
            self.allowed_car_type.currentData()
        )

        allowed_owner = (
            self.allowed_owner.text()
            .strip()
        )

        if not allowed_owner:

            allowed_owner = None

        return {
            "track_id": (
                self.track.id
                if self.track
                else None
            ),

            "spot_number": (
                self.spot_number.value()
            ),

            "name": (
                self.name.text()
                .strip()
                or None
            ),

            "description": (
                self.description.text()
                .strip()
                or None
            ),

            "max_length": max_length,

            "allowed_car_type": (
                allowed_car_type
            ),

            "allowed_owner": (
                allowed_owner
            ),

            "hazardous_allowed": (
                self.hazardous_allowed.isChecked()
            ),

            "load_only": (
                self.load_only.isChecked()
            ),

            "empty_only": (
                self.empty_only.isChecked()
            ),

            "notes": (
                self.notes.text()
                .strip()
                or None
            ),
        }