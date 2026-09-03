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
        "Empty Weight (lb)",
        "Load Limit (lb)",
        "Max Gross (lb)",
        "Status",
        "Current Location",
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

                    owner = (
                        normalized_row.get(
                            "owner",
                            "",
                        )
                    )

                    car_type = (
                        normalized_row.get(
                            "car_type",
                            "",
                        )
                        or normalized_row.get(
                            "type",
                            "",
                        )
                    )

                    length = (
                        normalized_row.get(
                            "length"
                        )
                    )

                    empty_weight_lbs = (
                        normalized_row.get(
                            "empty_weight_lbs"
                        )
                        or normalized_row.get(
                            "empty_weight_(lb)"
                        )
                        or normalized_row.get(
                            "empty_weight"
                        )
                        or normalized_row.get(
                            "lt_wt"
                        )
                    )

                    load_limit_lbs = (
                        normalized_row.get(
                            "load_limit_lbs"
                        )
                        or normalized_row.get(
                            "load_limit_(lb)"
                        )
                        or normalized_row.get(
                            "load_limit"
                        )
                        or normalized_row.get(
                            "ld_lmt"
                        )
                    )

                    status = (
                        normalized_row.get(
                            "status",
                            "Available",
                        )
                        or "Available"
                    )

                    location = (
                        normalized_row.get(
                            "location",
                            "",
                        )
                        or normalized_row.get(
                            "current_location",
                            "",
                        )
                    )

                    #
                    # Required fields.
                    #

                    if (
                        not reporting_mark
                        or not number
                    ):

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
                    # Convert weight fields to integers
                    # when supplied.
                    #

                    if empty_weight_lbs:

                        empty_weight_lbs = int(
                            str(
                                empty_weight_lbs
                            ).replace(
                                ",",
                                "",
                            )
                        )

                    else:

                        empty_weight_lbs = None

                    if load_limit_lbs:

                        load_limit_lbs = int(
                            str(
                                load_limit_lbs
                            ).replace(
                                ",",
                                "",
                            )
                        )

                    else:

                        load_limit_lbs = None

                    #
                    # Check whether the car already exists.
                    #
                    # Reporting Mark + Number uniquely
                    # identifies a freight car.
                    #

                    existing_car = (
                        CarService.get_by_reporting_mark_and_number(
                            reporting_mark,
                            number,
                        )
                    )

                    if existing_car is not None:

                        #
                        # Existing cars are updated using
                        # safe-merge behavior.
                        #
                        # A populated CSV field replaces the
                        # current database value.
                        #
                        # A blank CSV field preserves the
                        # current database value.
                        #
                        # Operational status and location are
                        # always preserved from the database.
                        #

                        updated_owner = (
                            owner
                            if owner
                            else existing_car.owner
                        )

                        updated_car_type = (
                            car_type
                            if car_type
                            else existing_car.car_type
                        )

                        updated_length = (
                            length
                            if length is not None
                            else existing_car.length
                        )

                        updated_empty_weight_lbs = (
                            empty_weight_lbs
                            if empty_weight_lbs is not None
                            else existing_car.empty_weight_lbs
                        )

                        updated_load_limit_lbs = (
                            load_limit_lbs
                            if load_limit_lbs is not None
                            else existing_car.load_limit_lbs
                        )

                        updated_car = CarService.update(
                            car_id=existing_car.id,
                            reporting_mark=existing_car.reporting_mark,
                            number=existing_car.number,
                            owner=updated_owner,
                            car_type=updated_car_type,
                            length=updated_length,
                            empty_weight_lbs=updated_empty_weight_lbs,
                            load_limit_lbs=updated_load_limit_lbs,
                            status=existing_car.status,
                            location=existing_car.location,
                        )

                        if updated_car is not None:

                            added += 1

                        else:

                            skipped += 1

                        continue

                    #
                    # Car does not already exist.
                    #
                    # For a new car, blank optional CSV
                    # fields remain blank.
                    #

                    car = CarService.add(
                        reporting_mark=reporting_mark,
                        number=number,
                        owner=owner,
                        car_type=car_type,
                        length=length,
                        empty_weight_lbs=empty_weight_lbs,
                        load_limit_lbs=load_limit_lbs,
                        status=status,
                        location=location,
                    )

                    if car:

                        added += 1

                    else:

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
        filename,
    ):

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8",
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
                "Empty Weight (lb)",
                "Load Limit (lb)",
                "Max Gross (lb)",
                "Status",
                "Current Location",
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
                        "",
                    ),
                    getattr(
                        car,
                        "empty_weight_lbs",
                        "",
                    ),
                    getattr(
                        car,
                        "load_limit_lbs",
                        "",
                    ),
                    getattr(
                        car,
                        "maximum_gross_weight_lbs",
                        "",
                    ),
                    car.status,
                    car.location,
                ])

    # ---------------------------------------------------------
    # Row count
    # ---------------------------------------------------------

    def rowCount(
        self,
        parent=None,
    ):

        return len(
            self.cars
        )

    # ---------------------------------------------------------
    # Column count
    # ---------------------------------------------------------

    def columnCount(
        self,
        parent=None,
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
        role,
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
        role,
    ):

        if not index.isValid():

            return None

        car = self.cars[
            index.row()
        ]

        STATUS_MAP = {

            "available": (
                "🟢",
                "Available",
            ),

            "loaded": (
                "🔵",
                "Loaded",
            ),

            "empty": (
                "🟡",
                "Empty",
            ),

            "in shop": (
                "🔴",
                "In Shop",
            ),

            "interchange track": (
                "🟣",
                "Interchange",
            ),

        }

        key = (
            car.status or ""
        ).strip().lower()

        emoji, display = STATUS_MAP.get(
            key,
            (
                "",
                car.status or "",
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
                        "",
                    )

                case 5:

                    return getattr(
                        car,
                        "empty_weight_lbs",
                        "",
                    )

                case 6:

                    return getattr(
                        car,
                        "load_limit_lbs",
                        "",
                    )

                case 7:

                    return getattr(
                        car,
                        "maximum_gross_weight_lbs",
                        "",
                    )

                case 8:

                    return (
                        f"{emoji} {display}"
                    ).strip()

                case 9:

                    return car.location

        #
        # Keep status text readable
        # with selection highlight.
        #

        if (
            role == Qt.ForegroundRole
            and index.column() == 8
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
        row,
    ):

        if 0 <= row < len(
            self.cars
        ):

            return self.cars[
                row
            ]

        return None