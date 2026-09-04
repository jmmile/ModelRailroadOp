from PySide6.QtCore import (
    QAbstractTableModel,
    Qt,
)

from modelrailroadops.services.switch_list_service import (
    SwitchListService,
)


class SwitchListTableModel(QAbstractTableModel):
    """
    Table model used to display operator-facing switch-list
    instructions.

    Each row represents one generated CarMove rather than one
    Waybill.

    A Waybill will normally produce two rows:

        PICKUP
        SETOUT

    The model may display all Trains assigned to an Operations
    Session or filter the rows to one Train.

    The model does not modify the database.
    """

    HEADERS = [
        "Train",
        "Seq",
        "Move",
        "Car",
        "Type",
        "Length",
        "Car Status",
        "Location",
        "Move Status",
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
        self.train_id = None

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
                row.get(
                    "train",
                    "",
                ),
                row.get(
                    "route_sequence"
                ),
                row.get(
                    "move_type",
                    "",
                ),
                row.get(
                    "car",
                    "",
                ),
                row.get(
                    "car_type",
                    "",
                ),
                row.get(
                    "length",
                    "",
                ),
                row.get(
                    "status",
                    "",
                ),
                row.get(
                    "instruction_location",
                    "",
                ),
                row.get(
                    "move_status",
                    "",
                ),
                row.get(
                    "waybill_status",
                    "",
                ),
                row.get(
                    "move_notes",
                    "",
                )
                or row.get(
                    "notes",
                    "",
                ),
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
                    row.get(
                        "train",
                        "",
                    )
                    or ""
                ).casefold()

            if column == 1:
                sequence = row.get(
                    "route_sequence"
                )

                if sequence is None:
                    return 999999

                return sequence

            if column == 2:
                return (
                    row.get(
                        "move_type",
                        "",
                    )
                    or ""
                ).casefold()

            if column == 3:
                return (
                    row.get(
                        "car",
                        "",
                    )
                    or ""
                ).casefold()

            if column == 4:
                return (
                    row.get(
                        "car_type",
                        "",
                    )
                    or ""
                ).casefold()

            if column == 5:
                length = row.get(
                    "length"
                )

                if length in (
                    "",
                    None,
                ):
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
                    row.get(
                        "status",
                        "",
                    )
                    or ""
                ).casefold()

            if column == 7:
                return (
                    row.get(
                        "instruction_location",
                        "",
                    )
                    or ""
                ).casefold()

            if column == 8:
                return (
                    row.get(
                        "move_status",
                        "",
                    )
                    or ""
                ).casefold()

            if column == 9:
                return (
                    row.get(
                        "waybill_status",
                        "",
                    )
                    or ""
                ).casefold()

            if column == 10:
                return (
                    row.get(
                        "move_notes",
                        "",
                    )
                    or row.get(
                        "notes",
                        "",
                    )
                    or ""
                ).casefold()

        return None

    #
    # Sorting
    #

    def sort(
        self,
        column,
        order=Qt.AscendingOrder,
    ):
        """
        Sort switch-list rows using the displayed
        column's data type.
        """

        def text_value(
            row,
            key,
        ):
            return str(
                row.get(
                    key
                )
                or ""
            ).casefold()

        def number_value(
            row,
            key,
            missing=0,
        ):
            value = row.get(
                key
            )

            if value in (
                None,
                "",
            ):
                return missing

            try:
                return float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):
                return missing

        def notes_value(
            row,
        ):
            return str(
                row.get(
                    "move_notes"
                )
                or row.get(
                    "notes"
                )
                or ""
            ).casefold()

        key_functions = {
            0: lambda row: text_value(
                row,
                "train",
            ),
            1: lambda row: number_value(
                row,
                "route_sequence",
                999999,
            ),
            2: lambda row: text_value(
                row,
                "move_type",
            ),
            3: lambda row: text_value(
                row,
                "car",
            ),
            4: lambda row: text_value(
                row,
                "car_type",
            ),
            5: lambda row: number_value(
                row,
                "length",
            ),
            6: lambda row: text_value(
                row,
                "status",
            ),
            7: lambda row: text_value(
                row,
                "instruction_location",
            ),
            8: lambda row: text_value(
                row,
                "move_status",
            ),
            9: lambda row: text_value(
                row,
                "waybill_status",
            ),
            10: notes_value,
        }

        key_function = (
            key_functions.get(
                column
            )
        )

        if key_function is None:
            return

        self.layoutAboutToBeChanged.emit()

        self.rows.sort(
            key=key_function,
            reverse=(
                order
                == Qt.DescendingOrder
            ),
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
    # Set Train
    #

    def set_train(
        self,
        train_id,
    ):
        """
        Filter the model to one Train.

        Pass None to display all Trains in the selected
        Operations Session.
        """

        self.train_id = (
            train_id
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
                    self.operations_session_id,
                    train_id=self.train_id,
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
    # Get CarMove ID
    #

    def get_car_move_id(
        self,
        row,
    ):
        """
        Return the CarMove ID represented by the
        selected switch-list row.
        """

        data = self.get_row(
            row
        )

        if data is None:
            return None

        return data.get(
            "car_move_id"
        )

    #
    # Get Waybill ID
    #

    def get_waybill_id(
        self,
        row,
    ):
        """
        Return the Waybill associated with the selected
        CarMove.

        Retained for compatibility with other UI code.
        """

        data = self.get_row(
            row
        )

        if data is None:
            return None

        return data.get(
            "waybill_id"
        )

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

        return data.get(
            "car_id"
        )

    #
    # Get Train ID
    #

    def get_train_id(
        self,
        row,
    ):
        data = self.get_row(
            row
        )

        if data is None:
            return None

        return data.get(
            "train_id"
        )

    #
    # Get move type
    #

    def get_move_type(
        self,
        row,
    ):
        data = self.get_row(
            row
        )

        if data is None:
            return None

        return data.get(
            "move_type"
        )

    #
    # Get move status
    #

    def get_move_status(
        self,
        row,
    ):
        data = self.get_row(
            row
        )

        if data is None:
            return None

        return data.get(
            "move_status"
        )

    #
    # Get route sequence
    #

    def get_route_sequence(
        self,
        row,
    ):
        data = self.get_row(
            row
        )

        if data is None:
            return None

        return data.get(
            "route_sequence"
        )

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
                    "",
                )
                or ""
            ),
            "track": (
                data.get(
                    "destination_track",
                    "",
                )
                or ""
            ),
            "spot": (
                data.get(
                    "destination_spot",
                    "",
                )
                or ""
            ),
        }

    #
    # Get instruction location
    #

    def get_instruction_location(
        self,
        row,
    ):
        data = self.get_row(
            row
        )

        if data is None:
            return None

        return (
            data.get(
                "instruction_location",
                "",
            )
            or ""
        )