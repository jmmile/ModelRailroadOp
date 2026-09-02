from PySide6.QtCore import QAbstractTableModel, Qt

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car


class CarLocationTableModel(QAbstractTableModel):
    """Display cars at general locations, tracks, and industry spots."""

    HEADERS = [
        "Car",
        "Type",
        "Location",
        "Location Type",
        "Track",
        "Traffic Use",
        "Industry",
        "Spot",
    ]

    def __init__(self):
        super().__init__()
        self.rows = []
        self.sort_column = 0
        self.sort_order = Qt.AscendingOrder
        self.load_data()

    def load_data(self):
        self.beginResetModel()
        self.rows = []

        with SessionLocal() as session:
            cars = (
                session.query(Car)
                .order_by(Car.reporting_mark, Car.number)
                .all()
            )

            for car in cars:
                operating_location = car.operating_location
                operating_track = car.operating_track

                location_name = (
                    operating_location.name
                    if operating_location is not None
                    else (
                        car.industry.name
                        if car.industry is not None
                        else (car.location or "Unassigned")
                    )
                )
                location_type = (
                    operating_location.location_type.title()
                    if operating_location is not None
                    else ("Industry" if car.industry is not None else "")
                )
                track_name = (
                    operating_track.name
                    if operating_track is not None
                    else (car.track.name if car.track is not None else "")
                )
                traffic_use = (
                    operating_track.traffic_use.title()
                    if operating_track is not None
                    else ""
                )
                industry_name = (
                    car.industry.name if car.industry is not None else ""
                )
                spot_number = (
                    car.spot.spot_number if car.spot is not None else None
                )

                values = [
                    f"{car.reporting_mark} {car.number}",
                    car.car_type or "",
                    location_name,
                    location_type,
                    track_name,
                    traffic_use,
                    industry_name,
                    str(spot_number) if spot_number is not None else "",
                ]

                self.rows.append(
                    {
                        "id": car.id,
                        "values": values,
                        "spot_number": spot_number,
                    }
                )

        self._sort_rows()
        self.endResetModel()

    def sort(self, column, order=Qt.AscendingOrder):
        if not 0 <= column < len(self.HEADERS):
            return
        self.layoutAboutToBeChanged.emit()
        self.sort_column = column
        self.sort_order = order
        self._sort_rows()
        self.layoutChanged.emit()

    def _sort_rows(self):
        reverse = self.sort_order == Qt.DescendingOrder

        if self.sort_column == 7:
            key = lambda row: (
                row["spot_number"] is None,
                row["spot_number"] or 0,
            )
        else:
            key = lambda row: str(
                row["values"][self.sort_column]
            ).casefold()

        self.rows.sort(key=key, reverse=reverse)

    def get_car_id(self, row):
        if not 0 <= row < len(self.rows):
            return None
        return self.rows[row]["id"]

    def find_row_by_car_id(self, car_id):
        for row_number, row in enumerate(self.rows):
            if row["id"] == car_id:
                return row_number
        return None

    def rowCount(self, parent=None):
        return len(self.rows)

    def columnCount(self, parent=None):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self.rows[index.row()]["values"][index.column()]
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return section + 1
