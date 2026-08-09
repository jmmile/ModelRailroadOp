
import csv

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
)

from PySide6.QtGui import QColor

from modelrailroadops.services.car_service import CarService


class CarTableModel(QAbstractTableModel):
    """
    Table model for the freight car roster.
    """

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

    # ---------------------------------------------------------
    # Refresh
    # ---------------------------------------------------------

    def refresh(self):

        self.beginResetModel()

        self.cars = CarService.get_all()

        self.endResetModel()

    # ---------------------------------------------------------
    # Import CSV
    # ---------------------------------------------------------

    def import_from_csv(
        self,
        filename
    ):

        added = 0
        skipped = 0

        with open(
            filename,
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                #
                # Normalize CSV column names.
                #
                # This allows both:
                #
                # Reporting Mark
                # reporting_mark
                #
                # and both:
                #
                # Type
                # car_type
                #

                normalized_row = {}

                for key, value in row.items():

                    if key is None:
                        continue

                    normalized_key = (
                        key.strip()
                        .lower()
                        .replace(
                            " ",
                            "_"
                        )
                    )

                    normalized_row[
                        normalized_key
                    ] = (
                        value.strip()
                        if isinstance(
                            value,
                            str
                        )
                        else value
                    )

                try:

                    reporting_mark = (
                        normalized_row.get(
                            "reporting_mark",
                            ""
                        )
                    )

                    number = (
                        normalized_row.get(
                            "number",
                            ""
                        )
                    )

                    owner = (
                        normalized_row.get(
                            "owner",
                            ""
                        )
                    )

                    car_type = (
                        normalized_row.get(
                            "car_type",
                            ""
                        )
                        or normalized_row.get(
                            "type",
                            ""
                        )
                    )

                    length = (
                        normalized_row.get(
                            "length"
                        )
                    )

                    status = (
                        normalized_row.get(
                            "status",
                            "Available"
                        )
                        or "Available"
                    )

                    location = (
                        normalized_row.get(
                            "location",
                            ""
                        )
                    )

                    #
                    # Required fields.
                    #

                    if not reporting_mark or not number:

                        skipped += 1

                        continue

                    #
                    # Convert length to an integer
                    # when supplied.
                    #

                    if length:

                        length = int(
                            length
                        )

                    else:

                        length = None

                    #
                    # Add the car.
                    #

                    car = CarService.add(
                        reporting_mark=reporting_mark,
                        number=number,
                        owner=owner,
                        car_type=car_type,
                        length=length,
                        status=status,
                        location=location,
                    )

                    if car:

                        added += 1

                    else:

                        #
                        # Car already exists.
                        #

                        skipped += 1

                except Exception:

                    skipped += 1

        #
        # Reload the table from the database.
        #

        self.refresh()

        return added, skipped

    # ---------------------------------------------------------
    # Export CSV
    # ---------------------------------------------------------

    def export_to_csv(
        self,
        filename
    ):

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            #
            # CSV column names
            #

            writer.writerow([
                "Reporting Mark",
                "Number",
                "Owner",
                "Type",
                "Length",
                "Status",
                "Location",
            ])

            #
            # Write every car.
            #

            for car in self.cars:

                writer.writerow([
                    car.reporting_mark,
                    car.number,
                    car.owner,
                    car.car_type,
                    getattr(
                        car,
                        "length",
                        ""
                    ),
                    car.status,
                    car.location,
                ])

    # ---------------------------------------------------------
    # Row count
    # ---------------------------------------------------------

    def rowCount(
        self,
        parent=None
    ):

        return len(
            self.cars
        )

    # ---------------------------------------------------------
    # Column count
    # ---------------------------------------------------------

    def columnCount(
        self,
        parent=None
    ):

        return len(
            self.HEADERS
        )

    # ---------------------------------------------------------
    # Header data
    # ---------------------------------------------------------

    def headerData(
        self,
        section,
        orientation,
        role
    ):

        if role != Qt.DisplayRole:

            return None

        if orientation == Qt.Horizontal:

            return self.HEADERS[
                section
            ]

        return section + 1

    # ---------------------------------------------------------
    # Table data
    # ---------------------------------------------------------

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
        # with selection highlight.
        #

        if (
            role == Qt.ForegroundRole
            and index.column() == 5
        ):

            return QColor(
                "black"
            )

        return None

    # ---------------------------------------------------------
    # Get car
    # ---------------------------------------------------------

    def get_car(
        self,
        row
    ):

        if 0 <= row < len(
            self.cars
        ):

            return self.cars[
                row
            ]

        return None
