import csv

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
)

from PySide6.QtGui import QColor

from modelrailroadops.services.car_service import CarService


class CarTableModel(QAbstractTableModel):

    HEADERS = [
        "Reporting Mark",
        "Number",
        "Owner",
        "Type",
        "Length",
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



    def import_from_csv(
        self,
        filename
    ):

        added = 0
        skipped = 0


        with open(
            filename,
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)


            for row in reader:

                try:

                    car = CarService.add(
                        reporting_mark=row["reporting_mark"],
                        number=row["number"],
                        owner=row.get(
                            "owner",
                            ""
                        ),
                        car_type=row.get(
                            "car_type",
                            ""
                        ),
                        length=row.get(
                            "length"
                        ),
                        status=row.get(
                            "status",
                            "Available"
                        ),
                        location=row.get(
                            "location",
                            ""
                        ),
                    )


                    if car:

                        added += 1

                    else:

                        skipped += 1


                except Exception:

                    skipped += 1



        self.refresh()


        return added, skipped



    def rowCount(
        self,
        parent=None
    ):

        return len(self.cars)



    def columnCount(
        self,
        parent=None
    ):

        return len(self.HEADERS)



    def headerData(
        self,
        section,
        orientation,
        role
    ):

        if role != Qt.DisplayRole:

            return None


        if orientation == Qt.Horizontal:

            return self.HEADERS[section]


        return section + 1



    def data(
        self,
        index,
        role
    ):

        if not index.isValid():

            return None


        car = self.cars[
            index.row()
        ]


        STATUS_MAP = {

            "available": (
                "🟢",
                "Available"
            ),

            "loaded": (
                "🔵",
                "Loaded"
            ),

            "empty": (
                "🟡",
                "Empty"
            ),

            "in shop": (
                "🔴",
                "In Shop"
            ),

            "interchange track": (
                "🟣",
                "Interchange"
            ),

        }


        key = (
            car.status or ""
        ).strip().lower()


        emoji, display = STATUS_MAP.get(
            key,
            (
                "",
                car.status or ""
            )
        )


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

                    return getattr(
                        car,
                        "length",
                        ""
                    )


                case 5:

                    return (
                        f"{emoji} {display}"
                    ).strip()


                case 6:

                    return car.location



        #
        # Keep status text readable
        # with selection highlight
        #

        if (
            role == Qt.ForegroundRole
            and index.column() == 5
        ):

            return QColor(
                "black"
            )


        return None



    def get_car(
        self,
        row
    ):

        if 0 <= row < len(self.cars):

            return self.cars[row]


        return None