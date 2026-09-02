from PySide6.QtCore import (
    QAbstractTableModel,
    Qt,
)


class CarMoveTableModel(QAbstractTableModel):
    """
    Table model used to display CarMove records.

    CarMove records are supplied through set_moves().
    The model does not modify the database.
    """

    HEADERS = [
        "Move",
        "Train",
        "Car",
        "Move Type",
        "Route Seq",
        "Origin",
        "Destination",
        "Waybill",
    ]

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.moves = []

    #
    # Row count
    #

    def rowCount(
        self,
        parent=None,
    ):

        return len(
            self.moves
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
            index.row() < 0
            or index.row() >= len(self.moves)
        ):

            return None

        move = self.moves[
            index.row()
        ]

        #
        # Display data
        #

        if role == Qt.DisplayRole:

            values = [
                move.id,
                self.get_train_display(
                    move
                ),
                self.get_car_display(
                    move
                ),
                move.move_type,
                move.route_sequence,
                move.origin_location,
                move.destination_location,
                self.get_waybill_display(
                    move
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
                    move.id
                    if move.id is not None
                    else 0
                )

            if column == 1:

                return self.get_train_display(
                    move
                ).casefold()

            if column == 2:

                return self.get_car_display(
                    move
                ).casefold()

            if column == 3:

                return (
                    move.move_type
                    or ""
                ).casefold()

            if column == 4:

                return (
                    move.route_sequence
                    if move.route_sequence is not None
                    else 0
                )

            if column == 5:

                return (
                    move.origin_location
                    or ""
                ).casefold()

            if column == 6:

                return (
                    move.destination_location
                    or ""
                ).casefold()

            if column == 7:

                return self.get_waybill_display(
                    move
                ).casefold()

        return None

    #
    # Train display
    #

    @staticmethod
    def get_train_display(
        move,
    ):

        train = getattr(
            move,
            "train",
            None,
        )

        if train is not None:

            number = (
                getattr(
                    train,
                    "number",
                    None,
                )
                or ""
            )

            name = (
                getattr(
                    train,
                    "name",
                    None,
                )
                or ""
            )

            if number and name:

                return (
                    f"{number} - {name}"
                )

            return (
                number
                or name
            )

        train_id = getattr(
            move,
            "train_id",
            None,
        )

        if train_id is None:

            return ""

        return str(
            train_id
        )

    #
    # Car display
    #

    @staticmethod
    def get_car_display(
        move,
    ):

        car = getattr(
            move,
            "car",
            None,
        )

        if car is not None:

            reporting_mark = (
                getattr(
                    car,
                    "reporting_mark",
                    None,
                )
                or ""
            )

            number = (
                getattr(
                    car,
                    "number",
                    None,
                )
                or ""
            )

            if reporting_mark and number:

                return (
                    f"{reporting_mark} "
                    f"{number}"
                )

            return (
                reporting_mark
                or str(number)
                if number
                else ""
            )

        car_id = getattr(
            move,
            "car_id",
            None,
        )

        if car_id is None:

            return ""

        return str(
            car_id
        )

    #
    # Waybill display
    #

    @staticmethod
    def get_waybill_display(
        move,
    ):

        waybill = getattr(
            move,
            "waybill",
            None,
        )

        if waybill is not None:

            waybill_id = getattr(
                waybill,
                "id",
                None,
            )

            if waybill_id is not None:

                return str(
                    waybill_id
                )

        waybill_id = getattr(
            move,
            "waybill_id",
            None,
        )

        if waybill_id is None:

            return ""

        return str(
            waybill_id
        )

    #
    # Set moves
    #

    def set_moves(
        self,
        moves,
    ):

        self.beginResetModel()

        self.moves = list(
            moves
        )

        self.endResetModel()

    #
    # Get move
    #

    def get_move(
        self,
        row,
    ):

        if (
            row < 0
            or row >= len(self.moves)
        ):

            return None

        return self.moves[
            row
        ]

    #
    # Get move ID
    #

    def get_move_id(
        self,
        row,
    ):

        move = self.get_move(
            row
        )

        if move is None:

            return None

        return move.id
