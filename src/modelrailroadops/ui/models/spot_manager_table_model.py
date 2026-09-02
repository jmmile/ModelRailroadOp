from PySide6.QtCore import (
    QAbstractTableModel,
    Qt,
)

from PySide6.QtGui import (
    QColor,
    QBrush,
)

from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.spot import Spot
from modelrailroadops.models.industry_track import IndustryTrack

from modelrailroadops.services.spot_service import SpotService


class SpotManagerTableModel(QAbstractTableModel):

    HEADERS = [
        "Industry",
        "Track",
        "Spot",
        "Car",
        "Car Type",
        "Length",
        "Allowed Type",
        "Allowed Owner",
        "Max Length",
        "Hazardous",
        "Load Only",
        "Empty Only",
        "Status",
    ]

    def __init__(self):

        super().__init__()

        self.rows = []

        self.show_violations_only = False

        self.load_data()

    def rowCount(
        self,
        parent=None,
    ):

        return len(self.rows)

    def columnCount(
        self,
        parent=None,
    ):

        return len(self.HEADERS)

    def headerData(
        self,
        section,
        orientation,
        role=Qt.DisplayRole,
    ):

        if (
            role == Qt.DisplayRole
            and orientation == Qt.Horizontal
        ):

            return self.HEADERS[
                section
            ]

        return None

    def data(
        self,
        index,
        role=Qt.DisplayRole,
    ):

        if not index.isValid():

            return None

        row = self.rows[
            index.row()
        ]

        if role == Qt.DisplayRole:

            values = [

                row["industry"],
                row["track"],
                row["spot"],
                row["car"],
                row["car_type"],
                row["length"],
                row["allowed_car_type"],
                row["allowed_owner"],
                row["max_length"],
                row["hazardous_allowed"],
                row["load_only"],
                row["empty_only"],
                row["restriction_status"],

            ]

            return values[
                index.column()
            ]

        #
        # Highlight violations
        #

        if role == Qt.BackgroundRole:

            if not row["restriction_ok"]:

                return QBrush(
                    QColor(
                        255,
                        200,
                        200,
                    )
                )

        if role == Qt.ForegroundRole:

            if (
                index.column() == 12
                and not row["restriction_ok"]
            ):

                return QBrush(
                    QColor(
                        180,
                        0,
                        0,
                    )
                )

        return None

    #
    # Violation filter
    #

    def set_violation_filter(
        self,
        enabled,
    ):

        self.show_violations_only = enabled

        self.load_data()

    #
    # Load data
    #

    def load_data(self):

        self.beginResetModel()

        self.rows = []

        with SessionLocal() as session:

            spots = (
                session.query(Spot)
                .options(
                    joinedload(
                        Spot.track
                    ).joinedload(
                        IndustryTrack.industry
                    ),
                    joinedload(
                        Spot.car
                    ),
                )
                .all()
            )

            for spot in spots:

                track = spot.track

                if track is None:
                    continue

                industry = track.industry

                if industry is None:
                    continue

                car = spot.car

                if car:

                    car_name = (
                        f"{car.reporting_mark} "
                        f"{car.number}"
                    )

                    car_type = (
                        car.car_type or ""
                    )

                    car_length = (
                        car.length
                        if car.length
                        else ""
                    )

                    car_id = car.id

                else:

                    car_name = "Empty"

                    car_type = ""

                    car_length = ""

                    car_id = None

                valid, message = (
                    SpotService.check_restriction_violation(
                        spot.id
                    )
                )

                status = (
                    "🟢 OK"
                    if valid
                    else
                    f"⚠ {message}"
                )

                if (
                    self.show_violations_only
                    and valid
                ):

                    continue

                self.rows.append(
                    {
                        "spot_id":
                            spot.id,

                        "car_id":
                            car_id,

                        "industry":
                            industry.name,

                        "track":
                            track.name,

                        "spot":
                            spot.spot_number,

                        "car":
                            car_name,

                        "car_type":
                            car_type,

                        "length":
                            car_length,

                        "allowed_car_type":
                            spot.allowed_car_type or "",

                        "allowed_owner":
                            spot.allowed_owner or "",

                        "max_length":
                            spot.max_length or "",

                        "hazardous_allowed":
                            (
                                "Yes"
                                if spot.hazardous_allowed
                                else "No"
                            ),

                        "load_only":
                            (
                                "Yes"
                                if spot.load_only
                                else "No"
                            ),

                        "empty_only":
                            (
                                "Yes"
                                if spot.empty_only
                                else "No"
                            ),

                        "restriction_status":
                            status,

                        "restriction_ok":
                            valid,
                    }
                )

        self.endResetModel()