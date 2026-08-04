from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot

from modelrailroadops.services.car_location_service import (
    CarLocationService
)


class AssignCarDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Assign Car"
        )

        self.resize(
            400,
            250
        )


        layout = QVBoxLayout(self)

        form = QFormLayout()


        self.car_combo = QComboBox()

        self.industry_combo = QComboBox()

        self.track_combo = QComboBox()

        self.spot_combo = QComboBox()


        form.addRow(
            "Car",
            self.car_combo
        )

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


        layout.addLayout(form)


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


        layout.addLayout(buttons)


        self.load_cars()

        self.load_industries()


        self.industry_combo.currentIndexChanged.connect(
            self.load_tracks
        )

        self.track_combo.currentIndexChanged.connect(
            self.load_spots
        )


        self.assign_button.clicked.connect(
            self.assign
        )

        self.cancel_button.clicked.connect(
            self.reject
        )


        # Initial population
        self.load_tracks()



    def load_cars(self):

        self.car_combo.clear()

        with SessionLocal() as session:

            cars = (
                session.query(Car)
                .filter(
                    Car.spot_id.is_(None)
                )
                .order_by(
                    Car.reporting_mark,
                    Car.number,
                )
                .all()
            )


            for car in cars:

                self.car_combo.addItem(
                    f"{car.reporting_mark} {car.number}",
                    car.id
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


            occupied = (
                session.query(Car.spot_id)
                .filter(
                    Car.spot_id.isnot(None)
                )
                .all()
            )


            occupied_ids = {
                row[0]
                for row in occupied
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

                if spot.id not in occupied_ids:

                    self.spot_combo.addItem(
                        f"Spot {spot.spot_number}",
                        spot.id
                    )



    def assign(self):

        car_id = (
            self.car_combo.currentData()
        )

        spot_id = (
            self.spot_combo.currentData()
        )


        if car_id is None or spot_id is None:

            QMessageBox.warning(
                self,
                "Missing Selection",
                "Please select a car and an available spot."
            )

            return



        result = (
            CarLocationService.assign_car_to_spot(
                car_id,
                spot_id
            )
        )


        if result:

            self.accept()

        else:

            QMessageBox.warning(
                self,
                "Assignment Failed",
                "The selected spot is already occupied."
            )