import csv

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
)

from PySide6.QtGui import QColor

from modelrailroadops.services.passenger_car_service import (
    PassengerCarService,
)


class PassengerCarTableModel(QAbstractTableModel):
    """
    Table model for the passenger equipment roster.
    """

    HEADERS = [
        "Reporting Mark",
        "Number",
        "Name",
        "Owner",
        "Equipment Type",
        "Length",
        "Status",
    ]

    def __init__(self):

        super().__init__()

        self.passenger_cars = []

        self.refresh()

    def refresh(self):

        self.beginResetModel()

        self.passenger_cars = PassengerCarService.get_all()

        self.endResetModel()

    def import_from_csv(
        self,
        filename,
    ):

        added = 0
        skipped = 0

        with open(
            filename,
            newline="",
            encoding="utf-8-sig",
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                normalized_row = {}

                for key, value in row.items():

                    if key is None:
                        continue

                    normalized_key = (
                        key.strip()
                        .lower()
                        .replace(
                            " ",
                            "_",
                        )
                    )

                    normalized_row[
                        normalized_key
                    ] = (
                        value.strip()
                        if isinstance(
                            value,
                            str,
                        )
                        else value
                    )

                try:

                    reporting_mark = (
                        normalized_row.get(
                            "reporting_mark",
                            "",
                        )
                    )

                    number = (
                        normalized_row.get(
                            "number",
                            "",
                        )
                    )

                    name = (
                        normalized_row.get(
                            "name",
                            "",
                        )
                    )

                    owner = (
                        normalized_row.get(
                            "owner",
                            "",
                        )
                    )

                    equipment_type = (
                        normalized_row.get(
                            "equipment_type",
                            "",
                        )
                        or normalized_row.get(
                            "type",
                            "",
                        )
                        or "Coach"
                    )

                    length = (
                        normalized_row.get(
                            "length",
                        )
                    )

                    status = (
                        normalized_row.get(
                            "status",
                            "AVAILABLE",
                        )
                        or "AVAILABLE"
                    )

                    notes = (
                        normalized_row.get(
                            "notes",
                            "",
                        )
                    )

                    if not reporting_mark or not number:

                        skipped += 1

                        continue

                    if length:

                        length = int(
                            length
                        )

                    else:

                        length = None

                    passenger_car = PassengerCarService.add(
                        reporting_mark=reporting_mark,
                        number=number,
                        name=name,
                        owner=owner,
                        equipment_type=equipment_type,
                        length=length,
                        status=status,
                        notes=notes,
                    )

                    if passenger_car:

                        added += 1

                    else:

                        skipped += 1

                except Exception:

                    skipped += 1

        self.refresh()

        return added, skipped

    def export_to_csv(
        self,
        filename,
    ):

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.writer(
                file
            )

            writer.writerow([
                "Reporting Mark",
                "Number",
                "Name",
                "Owner",
                "Equipment Type",
                "Length",
                "Status",
                "Notes",
            ])

            for passenger_car in self.passenger_cars:

                writer.writerow([
                    passenger_car.reporting_mark,
                    passenger_car.number,
                    passenger_car.name,
                    passenger_car.owner,
                    passenger_car.equipment_type,
                    passenger_car.length,
                    passenger_car.status,
                    passenger_car.notes,
                ])

    def rowCount(
        self,
        parent=None,
    ):

        return len(
            self.passenger_cars
        )

    def columnCount(
        self,
        parent=None,
    ):

        return len(
            self.HEADERS
        )

    def headerData(
        self,
        section,
        orientation,
        role,
    ):

        if role != Qt.DisplayRole:

            return None

        if orientation == Qt.Horizontal:

            return self.HEADERS[
                section
            ]

        return section + 1

    def data(
        self,
        index,
        role,
    ):

        if not index.isValid():

            return None

        passenger_car = self.passenger_cars[
            index.row()
        ]

        status_map = {
            "available": (
                "🟢",
                "Available",
            ),
            "assigned": (
                "🔵",
                "Assigned",
            ),
            "out_of_service": (
                "🔴",
                "Out of Service",
            ),
            "out of service": (
                "🔴",
                "Out of Service",
            ),
        }

        key = (
            passenger_car.status or ""
        ).strip().lower()

        emoji, display = status_map.get(
            key,
            (
                "",
                passenger_car.status or "",
            ),
        )

        if role == Qt.DisplayRole:

            match index.column():

                case 0:

                    return passenger_car.reporting_mark

                case 1:

                    return passenger_car.number

                case 2:

                    return passenger_car.name or ""

                case 3:

                    return passenger_car.owner or ""

                case 4:

                    return passenger_car.equipment_type

                case 5:

                    return (
                        passenger_car.length
                        if passenger_car.length is not None
                        else ""
                    )

                case 6:

                    return (
                        f"{emoji} {display}"
                    ).strip()

        if (
            role == Qt.ForegroundRole
            and index.column() == 6
        ):

            return QColor(
                "black"
            )

        return None

    def get_passenger_car(
        self,
        row,
    ):

        if 0 <= row < len(
            self.passenger_cars
        ):

            return self.passenger_cars[
                row
            ]

        return None