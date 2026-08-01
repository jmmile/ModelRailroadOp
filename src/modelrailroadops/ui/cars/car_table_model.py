from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
)
from PySide6.QtGui import QColor, QBrush
from alembic.util import status
from sqlalchemy import case

from modelrailroadops.services.car_service import CarService


class CarTableModel(QAbstractTableModel):

    HEADERS = [
        "Reporting Mark",
        "Number",
        "Owner",
        "Type",
        "Status",
        "Location",
    ]

    def __init__(self):
        super().__init__()
        self.cars = []
        self.refresh()

    def refresh(self):
        self.beginResetModel()
        self.cars = CarService.get_all()
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self.cars)

    def columnCount(self, parent=None):
        return len(self.HEADERS)

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.HEADERS[section]

        return section + 1

    def data(self, index, role):
        if not index.isValid():
            return None

        car = self.cars[index.row()]

        STATUS_MAP = {
            "available": ("🟢", "Available", QColor("lightgreen")),
            "loaded": ("🔵", "Loaded", QColor("lightblue")),
            "empty": ("🟡", "Empty", QColor("khaki")),
            "in shop": ("🔴", "In Shop", QColor("salmon")),
            "interchange track": ("🟣", "Interchange", QColor("plum")),
        }

        key = (car.status or "").strip().lower()
        emoji, display, bg_color = STATUS_MAP.get(key, ("", car.status or "", None))

    # Text display
        if role == Qt.DisplayRole:
            match index.column():
                case 0: return car.reporting_mark
                case 1: return car.number
                case 2: return car.owner
                case 3: return car.car_type
                case 4: return f"{emoji} {display}".strip()
                case 5: return car.location

    # Background color for status column
        #if role == Qt.BackgroundRole and index.column() == 4:
        #    return bg_color
        
    # Foreground color (text color) for dark backgrounds
        if role == Qt.ForegroundRole and index.column() == 4:
            if bg_color in (QColor("salmon"), QColor("plum")):
                return QColor("black")






        return None

    def get_car(self, row):
        if 0 <= row < len(self.cars):
            return self.cars[row]
        return None
