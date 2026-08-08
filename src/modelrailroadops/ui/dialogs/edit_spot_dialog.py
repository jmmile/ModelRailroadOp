from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QLineEdit,
    QCheckBox,
    QTextEdit,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.spot import Spot
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.car import Car

from modelrailroadops.services.spot_service import SpotService



class EditSpotDialog(QDialog):

    def __init__(
        self,
        spot_id,
        parent=None,
    ):

        super().__init__(parent)

        self.spot_id = spot_id


        self.setWindowTitle(
            "Edit Spot Definition"
        )


        self.resize(
            500,
            600
        )


        layout = QVBoxLayout(self)



        #
        # Spot information
        #

        self.industry_label = QLabel()
        self.track_label = QLabel()
        self.spot_label = QLabel()


        layout.addWidget(
            self.industry_label
        )

        layout.addWidget(
            self.track_label
        )

        layout.addWidget(
            self.spot_label
        )



        #
        # Fields
        #

        form = QFormLayout()



        self.name_edit = QLineEdit()

        self.description_edit = QLineEdit()



        self.car_type_combo = QComboBox()

        self.owner_edit = QLineEdit()



        self.max_length_spin = QSpinBox()

        self.max_length_spin.setRange(
            0,
            200
        )



        self.hazardous_check = QCheckBox(
            "Hazardous cars allowed"
        )


        self.load_only_check = QCheckBox(
            "Load only"
        )


        self.empty_only_check = QCheckBox(
            "Empty only"
        )


        self.notes_edit = QTextEdit()



        form.addRow(
            "Name",
            self.name_edit
        )


        form.addRow(
            "Description",
            self.description_edit
        )


        form.addRow(
            "Allowed Car Type",
            self.car_type_combo
        )


        form.addRow(
            "Allowed Owner",
            self.owner_edit
        )


        form.addRow(
            "Maximum Length",
            self.max_length_spin
        )


        form.addRow(
            self.hazardous_check
        )


        form.addRow(
            self.load_only_check
        )


        form.addRow(
            self.empty_only_check
        )


        form.addRow(
            "Notes",
            self.notes_edit
        )


        layout.addLayout(
            form
        )



        #
        # Buttons
        #

        button_layout = QHBoxLayout()


        save_button = QPushButton(
            "Save"
        )


        cancel_button = QPushButton(
            "Cancel"
        )


        button_layout.addStretch()


        button_layout.addWidget(
            save_button
        )


        button_layout.addWidget(
            cancel_button
        )


        layout.addLayout(
            button_layout
        )



        save_button.clicked.connect(
            self.save
        )


        cancel_button.clicked.connect(
            self.reject
        )



        self.load_car_types()

        self.load_spot()



    def load_car_types(self):

        self.car_type_combo.clear()


        self.car_type_combo.addItem(
            "Any",
            None
        )


        with SessionLocal() as session:

            car_types = sorted(
                {
                    row[0]
                    for row in session.query(
                        Car.car_type
                    )
                    .distinct()
                    .all()
                    if row[0]
                }
            )


        for car_type in car_types:

            self.car_type_combo.addItem(
                car_type,
                car_type
            )



    def load_spot(self):

        with SessionLocal() as session:

            spot = session.get(
                Spot,
                self.spot_id
            )


            if spot is None:

                QMessageBox.warning(
                    self,
                    "Error",
                    "Spot not found."
                )

                self.reject()
                return



            track = session.get(
                IndustryTrack,
                spot.track_id
            )


            industry = session.get(
                Industry,
                track.industry_id
            )



            self.industry_label.setText(
                f"Industry: {industry.name}"
            )


            self.track_label.setText(
                f"Track: {track.name}"
            )


            self.spot_label.setText(
                f"Spot: {spot.spot_number}"
            )



            self.name_edit.setText(
                spot.name or ""
            )


            self.description_edit.setText(
                spot.description or ""
            )


            self.owner_edit.setText(
                spot.allowed_owner or ""
            )


            self.max_length_spin.setValue(
                spot.max_length or 0
            )


            self.hazardous_check.setChecked(
                spot.hazardous_allowed
            )


            self.load_only_check.setChecked(
                spot.load_only
            )


            self.empty_only_check.setChecked(
                spot.empty_only
            )


            self.notes_edit.setText(
                spot.notes or ""
            )


            index = (
                self.car_type_combo.findData(
                    spot.allowed_car_type
                )
            )


            if index >= 0:

                self.car_type_combo.setCurrentIndex(
                    index
                )



    def save(self):

        max_length = (
            self.max_length_spin.value()
        )


        if max_length == 0:

            max_length = None



        SpotService.update(
            spot_id=self.spot_id,

            name=self.name_edit.text(),

            description=self.description_edit.text(),

            allowed_car_type=(
                self.car_type_combo.currentData()
            ),

            allowed_owner=(
                self.owner_edit.text()
                or None
            ),

            max_length=max_length,

            hazardous_allowed=(
                self.hazardous_check.isChecked()
            ),

            load_only=(
                self.load_only_check.isChecked()
            ),

            empty_only=(
                self.empty_only_check.isChecked()
            ),

            notes=(
                self.notes_edit.toPlainText()
                or None
            ),
        )


        self.accept()