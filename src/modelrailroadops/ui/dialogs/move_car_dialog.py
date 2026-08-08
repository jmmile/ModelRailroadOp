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
    CarLocationService
)



class MoveCarDialog(QDialog):

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
            400,
            250
        )


        layout = QVBoxLayout(self)


        self.car_label = QLabel()


        layout.addWidget(
            self.car_label
        )


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


        move_button.clicked.connect(
            self.move_car
        )


        cancel_button.clicked.connect(
            self.reject
        )


        self.load_car()

        self.load_industries()


        self.industry_combo.currentIndexChanged.connect(
            self.load_tracks
        )


        self.track_combo.currentIndexChanged.connect(
            self.load_spots
        )


        self.load_tracks()



    def load_car(self):

        with SessionLocal() as session:

            car = session.get(
                Car,
                self.car_id
            )


            if car:

                self.car_label.setText(
                    f"Move: {car.reporting_mark} {car.number}"
                )



    def load_industries(self):

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
                    IndustryTrack.industry_id == industry_id
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



    def load_spots(self):

        self.spot_combo.clear()


        track_id = (
            self.track_combo.currentData()
        )


        if track_id is None:
            return


        with SessionLocal() as session:

            occupied = {
                row[0]
                for row in (
                    session.query(Car.spot_id)
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

                if spot.id not in occupied:

                    self.spot_combo.addItem(
                        f"Spot {spot.spot_number}",
                        spot.id
                    )



    def move_car(self):

        spot_id = (
            self.spot_combo.currentData()
        )


        if spot_id is None:

            QMessageBox.warning(
                self,
                "No Spot",
                "Please select an available destination spot."
            )

            return


        result = (
            CarLocationService.move_car(
                self.car_id,
                spot_id
            )
        )


        if result:

            self.accept()

        else:

            QMessageBox.warning(
                self,
                "Move Failed",
                "Unable to move car."
            )