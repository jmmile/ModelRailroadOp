from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
)

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

        if role == Qt.DisplayRole:

            match index.column():

                case 0:
                    return car.reporting_mark

                case 1:
                    return car.number

                case 2:
                    return car.owner

                case 3:
                    return car.car_type

                case 4:
                    return car.status

                case 5:
                    return car.location

        return None
        
    def get_car(self, row):

        if 0 <= row < len(self.cars):
            return self.cars[row]

        return None