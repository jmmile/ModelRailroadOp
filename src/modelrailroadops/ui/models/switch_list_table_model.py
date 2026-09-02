
from PySide6.QtCore import (
    QAbstractTableModel,
    Qt,
)

from modelrailroadops.services.switch_list_service import (
    SwitchListService,
)


class SwitchListTableModel(QAbstractTableModel):
    """
    Table model used to display switch-list rows.

    The model receives an Operations Session ID and
    loads the corresponding active and in-progress
    Waybills through SwitchListService.

    The model does not modify the database.
    """

    HEADERS = [
        "Train",
        "Pickup Seq",
        "Setout Seq",
        "Car",
        "Type",
        "Length",
        "Status",
        "Origin",
        "Destination",
        "Track",
        "Spot",
        "Waybill Status",
        "Notes",
    ]

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.rows = []

        self.operations_session_id = None

    #
    # Row count
    #

    def rowCount(
        self,
        parent=None,
    ):

        return len(
            self.rows
        )

    #
    # Column count
    #

    def columnCount(
        self,
        parent=None,
    ):

        return len(
            self.HEADERS
        )

    #
    # Header
    #

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

            if (
                0
                <= section
                < len(self.HEADERS)
            ):

                return self.HEADERS[
                    section
                ]

        return None

    #
    # Data
    #

    def data(
        self,
        index,
        role=Qt.DisplayRole,
    ):

        if not index.isValid():

            return None

        if (
            index.row()
            >= len(self.rows)
        ):

            return None

        row = self.rows[
            index.row()
        ]

        #
        # Display data
        #

        if role == Qt.DisplayRole:

            values = [
                row["train"],
                row["pickup_sequence"],
                row["setout_sequence"],
                row["car"],
                row["car_type"],
                row["length"],
                row["status"],
                row["origin"],
                row["destination"],
                row["destination_track"],
                row["destination_spot"],
                row["waybill_status"],
                row["notes"],
            ]

            value = values[
                index.column()
            ]

            if value is None:

                return ""

            return str(
                value
            )

        #
        # Sorting data
        #

        if role == Qt.UserRole:

            column = index.column()

            if column == 0:

                return (
                    row["train"]
                    or ""
                ).casefold()

            if column == 1:

                return (
                    row["pickup_sequence"]
                    if row["pickup_sequence"] is not None
                    else 999999
                )

            if column == 2:

                return (
                    row["setout_sequence"]
                    if row["setout_sequence"] is not None
                    else 999999
                )

            if column == 3:

                return (
                    row["car"]
                    or ""
                ).casefold()

            if column == 4:

                return (
                    row["car_type"]
                    or ""
                ).casefold()

            if column == 5:

                length = row["length"]

                if length == "":

                    return 0

                try:

                    return float(
                        length
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    return 0

            if column == 6:

                return (
                    row["status"]
                    or ""
                ).casefold()

            if column == 7:

                return (
                    row["origin"]
                    or ""
                ).casefold()

            if column == 8:

                return (
                    row["destination"]
                    or ""
                ).casefold()

            if column == 9:

                return (
                    row["destination_track"]
                    or ""
                ).casefold()

            if column == 10:

                spot = (
                    row["destination_spot"]
                )

                if spot in (
                    "",
                    None,
                ):

                    return 0

                try:

                    return int(
                        spot
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    return 0

            if column == 11:

                return (
                    row["waybill_status"]
                    or ""
                ).casefold()

            if column == 12:

                return (
                    row["notes"]
                    or ""
                ).casefold()

        return None

    def sort(
        self,
        column,
        order=Qt.AscendingOrder,
    ):
        """Sort switch-list rows using the displayed column's data type."""

        def text_value(row, key):
            return str(row.get(key) or "").casefold()

        def number_value(row, key, missing=0):
            value = row.get(key)
            if value in (None, ""):
                return missing
            try:
                return float(value)
            except (TypeError, ValueError):
                return missing

        key_functions = {
            0: lambda row: text_value(row, "train"),
            1: lambda row: number_value(row, "pickup_sequence", 999999),
            2: lambda row: number_value(row, "setout_sequence", 999999),
            3: lambda row: text_value(row, "car"),
            4: lambda row: text_value(row, "car_type"),
            5: lambda row: number_value(row, "length"),
            6: lambda row: text_value(row, "status"),
            7: lambda row: text_value(row, "origin"),
            8: lambda row: text_value(row, "destination"),
            9: lambda row: text_value(row, "destination_track"),
            10: lambda row: number_value(row, "destination_spot"),
            11: lambda row: text_value(row, "waybill_status"),
            12: lambda row: text_value(row, "notes"),
        }

        key_function = key_functions.get(column)
        if key_function is None:
            return

        self.layoutAboutToBeChanged.emit()
        self.rows.sort(
            key=key_function,
            reverse=order == Qt.DescendingOrder,
        )
        self.layoutChanged.emit()

    #
    # Set Operations Session
    #

    def set_operations_session(
        self,
        operations_session_id,
    ):

        self.operations_session_id = (
            operations_session_id
        )

        self.load_data()

    #
    # Load switch-list data
    #

    def load_data(
        self,
    ):

        self.beginResetModel()

        if (
            self.operations_session_id
            is None
        ):

            self.rows = []

        else:

            self.rows = (
                SwitchListService.get_switch_list_rows(
                    self.operations_session_id
                )
            )

        self.endResetModel()

    #
    # Refresh
    #

    def refresh(
        self,
    ):

        self.load_data()

    #
    # Get row
    #

    def get_row(
        self,
        row,
    ):

        if (
            row < 0
            or row >= len(self.rows)
        ):

            return None

        return self.rows[
            row
        ]

    #
    # Get Waybill ID
    #

    def get_waybill_id(
        self,
        row,
    ):

        data = self.get_row(
            row
        )

        if data is None:

            return None

        return data[
            "waybill_id"
        ]

    #
    # Get Car ID
    #

    def get_car_id(
        self,
        row,
    ):

        data = self.get_row(
            row
        )

        if data is None:

            return None

        return data[
            "car_id"
        ]

    #
    # Get Destination Spot ID
    #

    def get_destination_spot_id(
        self,
        row,
    ):

        data = self.get_row(
            row
        )

        if data is None:

            return None

        return data.get(
            "destination_spot_id"
        )

    #
    # Get destination information
    #

    def get_destination(
        self,
        row,
    ):

        data = self.get_row(
            row
        )

        if data is None:

            return None

        return {
            "industry": (
                data.get(
                    "destination_industry",
                    ""
                )
                or ""
            ),
            "track": (
                data.get(
                    "destination_track",
                    ""
                )
                or ""
            ),
            "spot": (
                data.get(
                    "destination_spot",
                    ""
                )
                or ""
            ),
        }
