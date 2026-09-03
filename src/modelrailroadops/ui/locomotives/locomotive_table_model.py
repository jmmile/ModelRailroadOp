import csv

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
)

from PySide6.QtGui import QColor

from modelrailroadops.services.locomotive_service import (
    LocomotiveService,
)


class LocomotiveTableModel(QAbstractTableModel):
    """
    Table model for the motive power roster.
    """

    HEADERS = [
        "Reporting Mark",
        "Number",
        "Owner",
        "Model",
        "Manufacturer",
        "Type",
        "Horsepower",
        "DCC Address",
        "Length",
        "Status",
    ]

    def __init__(self):

        super().__init__()

        self.locomotives = []

        self.refresh()

    # ---------------------------------------------------------
    # Refresh
    # ---------------------------------------------------------

    def refresh(self):

        self.beginResetModel()

        self.locomotives = LocomotiveService.get_all()

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

                    model = (
                        normalized_row.get(
                            "model",
                            "",
                        )
                    )

                    manufacturer = (
                        normalized_row.get(
                            "manufacturer",
                            "",
                        )
                    )

                    locomotive_type = (
                        normalized_row.get(
                            "locomotive_type",
                            "",
                        )
                        or normalized_row.get(
                            "type",
                            "",
                        )
                        or "Diesel"
                    )

                    horsepower = (
                        normalized_row.get(
                            "horsepower",
                        )
                        or normalized_row.get(
                            "hp",
                        )
                    )

                    dcc_address = (
                        normalized_row.get(
                            "dcc_address",
                        )
                        or normalized_row.get(
                            "dcc_decoder_address",
                        )
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

                    if horsepower:

                        horsepower = int(
                            str(horsepower).replace(
                                ",",
                                "",
                            )
                        )

                    else:

                        horsepower = None

                    if dcc_address:

                        dcc_address = int(
                            str(dcc_address).replace(
                                ",",
                                "",
                            )
                        )

                    else:

                        dcc_address = None

                    if length:

                        length = int(
                            length
                        )

                    else:

                        length = None

                    locomotive = LocomotiveService.add(
                        reporting_mark=reporting_mark,
                        number=number,
                        owner=owner,
                        model=model,
                        manufacturer=manufacturer,
                        locomotive_type=locomotive_type,
                        horsepower=horsepower,
                        dcc_address=dcc_address,
                        length=length,
                        status=status,
                        notes=notes,
                    )

                    if locomotive:

                        added += 1

                    else:

                        skipped += 1

                except Exception:

                    skipped += 1

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

            writer = csv.writer(
                file
            )

            writer.writerow([
                "Reporting Mark",
                "Number",
                "Owner",
                "Model",
                "Manufacturer",
                "Type",
                "Horsepower",
                "DCC Address",
                "Length",
                "Status",
                "Notes",
            ])

            for locomotive in self.locomotives:

                writer.writerow([
                    locomotive.reporting_mark,
                    locomotive.number,
                    locomotive.owner,
                    locomotive.model,
                    locomotive.manufacturer,
                    locomotive.locomotive_type,
                    locomotive.horsepower,
                    locomotive.dcc_address,
                    locomotive.length,
                    locomotive.status,
                    locomotive.notes,
                ])

    # ---------------------------------------------------------
    # Row count
    # ---------------------------------------------------------

    def rowCount(
        self,
        parent=None,
    ):

        return len(
            self.locomotives
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

        locomotive = self.locomotives[
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
            locomotive.status or ""
        ).strip().lower()

        emoji, display = status_map.get(
            key,
            (
                "",
                locomotive.status or "",
            ),
        )

        if role == Qt.DisplayRole:

            match index.column():

                case 0:

                    return locomotive.reporting_mark

                case 1:

                    return locomotive.number

                case 2:

                    return locomotive.owner or ""

                case 3:

                    return locomotive.model or ""

                case 4:

                    return locomotive.manufacturer or ""

                case 5:

                    return locomotive.locomotive_type

                case 6:

                    return (
                        locomotive.horsepower
                        if locomotive.horsepower is not None
                        else ""
                    )

                case 7:

                    return (
                        locomotive.dcc_address
                        if locomotive.dcc_address is not None
                        else ""
                    )

                case 8:

                    return (
                        locomotive.length
                        if locomotive.length is not None
                        else ""
                    )

                case 9:

                    return (
                        f"{emoji} {display}"
                    ).strip()

        if (
            role == Qt.ForegroundRole
            and index.column() == 9
        ):

            return QColor(
                "black"
            )

        return None

    # ---------------------------------------------------------
    # Get locomotive
    # ---------------------------------------------------------

    def get_locomotive(
        self,
        row,
    ):

        if 0 <= row < len(
            self.locomotives
        ):

            return self.locomotives[
                row
            ]

        return None