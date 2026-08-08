from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFormLayout,
    QGroupBox,
)

from PySide6.QtCore import Qt

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.spot import Spot
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.car import Car

from modelrailroadops.services.spot_service import SpotService



class SpotDetailWidget(QWidget):

    def __init__(
        self,
        parent=None
    ):

        super().__init__(parent)


        layout = QVBoxLayout(self)



        #
        # Status
        #

        self.status_label = QLabel(
            "No Spot Selected"
        )


        self.status_label.setAlignment(
            Qt.AlignCenter
        )


        self.status_label.setStyleSheet(
            """
            font-size: 14px;
            font-weight: bold;
            padding: 6px;
            """
        )


        layout.addWidget(
            self.status_label
        )



        #
        # Spot Information
        #

        spot_group = QGroupBox(
            "Spot Information"
        )


        spot_form = QFormLayout()


        self.industry_label = QLabel("-")

        self.track_label = QLabel("-")

        self.spot_label = QLabel("-")

        self.name_label = QLabel("-")

        self.description_label = QLabel("-")


        spot_form.addRow(
            "Industry",
            self.industry_label
        )


        spot_form.addRow(
            "Track",
            self.track_label
        )


        spot_form.addRow(
            "Spot",
            self.spot_label
        )


        spot_form.addRow(
            "Name",
            self.name_label
        )


        spot_form.addRow(
            "Description",
            self.description_label
        )


        spot_group.setLayout(
            spot_form
        )


        layout.addWidget(
            spot_group
        )



        #
        # Current Car
        #

        car_group = QGroupBox(
            "Current Car"
        )


        car_form = QFormLayout()


        self.car_label = QLabel("-")

        self.car_type_label = QLabel("-")

        self.car_length_label = QLabel("-")


        car_form.addRow(
            "Car",
            self.car_label
        )


        car_form.addRow(
            "Type",
            self.car_type_label
        )


        car_form.addRow(
            "Length",
            self.car_length_label
        )


        car_group.setLayout(
            car_form
        )


        layout.addWidget(
            car_group
        )



        #
        # Restrictions
        #

        restriction_group = QGroupBox(
            "Restrictions"
        )


        restriction_form = QFormLayout()


        self.allowed_type_label = QLabel("-")

        self.allowed_owner_label = QLabel("-")

        self.max_length_label = QLabel("-")

        self.hazardous_label = QLabel("-")

        self.load_only_label = QLabel("-")

        self.empty_only_label = QLabel("-")


        restriction_form.addRow(
            "Allowed Type",
            self.allowed_type_label
        )


        restriction_form.addRow(
            "Allowed Owner",
            self.allowed_owner_label
        )


        restriction_form.addRow(
            "Max Length",
            self.max_length_label
        )


        restriction_form.addRow(
            "Hazardous",
            self.hazardous_label
        )


        restriction_form.addRow(
            "Load Only",
            self.load_only_label
        )


        restriction_form.addRow(
            "Empty Only",
            self.empty_only_label
        )


        restriction_group.setLayout(
            restriction_form
        )


        layout.addWidget(
            restriction_group
        )



        #
        # Track Occupancy Summary
        #

        track_group = QGroupBox(
            "Track Summary"
        )


        track_form = QFormLayout()


        self.track_capacity_label = QLabel("-")

        self.track_occupied_label = QLabel("-")

        self.track_available_label = QLabel("-")

        self.track_status_label = QLabel("-")


        track_form.addRow(
            "Capacity",
            self.track_capacity_label
        )


        track_form.addRow(
            "Occupied",
            self.track_occupied_label
        )


        track_form.addRow(
            "Available",
            self.track_available_label
        )


        track_form.addRow(
            "Status",
            self.track_status_label
        )


        track_group.setLayout(
            track_form
        )


        layout.addWidget(
            track_group
        )
        
                #
        # Notes
        #

        notes_group = QGroupBox(
            "Notes"
        )


        notes_layout = QVBoxLayout()


        self.notes_label = QLabel("-")


        self.notes_label.setWordWrap(
            True
        )


        notes_layout.addWidget(
            self.notes_label
        )


        notes_group.setLayout(
            notes_layout
        )


        layout.addWidget(
            notes_group
        )


        layout.addStretch()



    def clear(self):

        self.status_label.setText(
            "No Spot Selected"
        )


        self.industry_label.setText("-")

        self.track_label.setText("-")

        self.spot_label.setText("-")

        self.name_label.setText("-")

        self.description_label.setText("-")


        self.car_label.setText("-")

        self.car_type_label.setText("-")

        self.car_length_label.setText("-")


        self.allowed_type_label.setText("-")

        self.allowed_owner_label.setText("-")

        self.max_length_label.setText("-")

        self.hazardous_label.setText("-")

        self.load_only_label.setText("-")

        self.empty_only_label.setText("-")


        self.track_capacity_label.setText("-")

        self.track_occupied_label.setText("-")

        self.track_available_label.setText("-")

        self.track_status_label.setText("-")


        self.notes_label.setText("-")



    def set_spot(
        self,
        spot_id
    ):

        with SessionLocal() as session:


            spot = session.get(
                Spot,
                spot_id
            )


            if spot is None:

                self.clear()

                return



            track = session.get(
                IndustryTrack,
                spot.track_id
            )


            if track is None:

                self.clear()

                return



            industry = session.get(
                Industry,
                track.industry_id
            )


            if industry is None:

                self.clear()

                return



            #
            # Track occupancy summary
            #

            track_spots = (
                session.query(Spot)
                .filter(
                    Spot.track_id == track.id
                )
                .all()
            )


            capacity = len(track_spots)


            spot_ids = [
                s.id
                for s in track_spots
            ]


            occupied = (
                session.query(Car)
                .filter(
                    Car.spot_id.in_(spot_ids)
                )
                .count()
                if spot_ids
                else 0
            )


            available = (
                capacity - occupied
            )



            #
            # Current car
            #

            car = (
                session.query(Car)
                .filter(
                    Car.spot_id == spot.id
                )
                .first()
            )



            #
            # Spot information
            #

            self.industry_label.setText(
                industry.name
            )


            self.track_label.setText(
                track.name
            )


            self.spot_label.setText(
                str(spot.spot_number)
            )


            self.name_label.setText(
                spot.name or "-"
            )


            self.description_label.setText(
                spot.description or "-"
            )



            #
            # Car information
            #

            if car:

                self.car_label.setText(
                    (
                        f"{car.reporting_mark} "
                        f"{car.number}"
                    )
                )


                self.car_type_label.setText(
                    car.car_type or "-"
                )


                self.car_length_label.setText(
                    (
                        f"{car.length} ft"
                        if car.length
                        else "-"
                    )
                )

            else:

                self.car_label.setText(
                    "Empty"
                )

                self.car_type_label.setText(
                    "-"
                )

                self.car_length_label.setText(
                    "-"
                )



            #
            # Restrictions
            #

            self.allowed_type_label.setText(
                spot.allowed_car_type
                or "Any"
            )


            self.allowed_owner_label.setText(
                spot.allowed_owner
                or "Any"
            )


            self.max_length_label.setText(
                (
                    f"{spot.max_length} ft"
                    if spot.max_length
                    else "No Limit"
                )
            )


            self.hazardous_label.setText(
                "Yes"
                if spot.hazardous_allowed
                else "No"
            )


            self.load_only_label.setText(
                "Yes"
                if spot.load_only
                else "No"
            )


            self.empty_only_label.setText(
                "Yes"
                if spot.empty_only
                else "No"
            )



            self.notes_label.setText(
                spot.notes or "-"
            )



            #
            # Track summary display
            #

            self.track_capacity_label.setText(
                str(capacity)
            )


            self.track_occupied_label.setText(
                str(occupied)
            )


            self.track_available_label.setText(
                str(available)
            )


            if capacity == 0:

                self.track_status_label.setText(
                    "-"
                )

            elif available == 0:

                self.track_status_label.setText(
                    "🔴 FULL"
                )

            elif available <= capacity / 2:

                self.track_status_label.setText(
                    "🟡 LIMITED"
                )

            else:

                self.track_status_label.setText(
                    "🟢 AVAILABLE"
                )



            #
            # Restriction status
            #

            valid, message = (
                SpotService.check_restriction_violation(
                    spot.id
                )
            )


            if car is None:

                self.status_label.setText(
                    "🟢 EMPTY"
                )

                self.status_label.setStyleSheet(
                    "color: green; font-weight: bold;"
                )


            elif valid:

                self.status_label.setText(
                    "🔵 OCCUPIED - OK"
                )

                self.status_label.setStyleSheet(
                    "color: blue; font-weight: bold;"
                )


            else:

                self.status_label.setText(
                    "🔴 RESTRICTION VIOLATION"
                )

                self.status_label.setStyleSheet(
                    "color: red; font-weight: bold;"
                )