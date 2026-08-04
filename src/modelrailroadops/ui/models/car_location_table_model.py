from PySide6.QtCore import (
    QAbstractTableModel,
    Qt,
)

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car


class CarLocationTableModel(QAbstractTableModel):
    """
    Table model for displaying:

    Car -> Industry -> Track -> Spot
    """

    HEADERS = [
        "Car",
        "Type",
        "Industry",
        "Track",
        "Spot",
    ]

    def __init__(self):
        super().__init__()

        self.rows = []

        self.load_data()


    def load_data(self):
        """
        Load current car locations.
        """

        self.beginResetModel()

        self.rows = []

        with SessionLocal() as session:

            cars = (
                session.query(Car)
                .order_by(
                    Car.reporting_mark,
                    Car.number,
                )
                .all()
            )

            for car in cars:

                self.rows.append(
                    [
                        f"{car.reporting_mark} {car.number}",

                        car.car_type,

                        (
                            car.industry.name
                            if car.industry
                            else "Yard"
                        ),

                        (
                            car.track.name
                            if car.track
                            else ""
                        ),

                        (
                            str(car.spot.spot_number)
                            if car.spot
                            else ""
                        ),
                    ]
                )

        self.endResetModel()


    def rowCount(self, parent=None):
        return len(self.rows)


    def columnCount(self, parent=None):
        return len(self.HEADERS)


    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():
            return None


        if role == Qt.DisplayRole:

            return self.rows[
                index.row()
            ][
                index.column()
            ]

        return None


    def headerData(
        self,
        section,
        orientation,
        role=Qt.DisplayRole,
    ):

        if role != Qt.DisplayRole:
            return None


        if orientation == Qt.Horizontal:
            return self.HEADERS[section]


        return section + 1