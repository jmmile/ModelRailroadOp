import re

from PySide6.QtCore import (
    Qt,
)

from PySide6.QtGui import (
    QStandardItem,
    QStandardItemModel,
)


def natural_sort_key(value):
    """Sort embedded digits numerically while retaining text support."""

    return tuple(
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in re.split(r"(\d+)", str(value or ""))
        if part
    )


class SortableStandardItem(QStandardItem):

    def __init__(self, value, sort_value):

        super().__init__(
            str(value)
        )

        self.sort_value = sort_value

    def __lt__(self, other):

        if isinstance(other, SortableStandardItem):

            return (
                self.sort_value
                < other.sort_value
            )

        return super().__lt__(
            other
        )


class TrainTableModel(QStandardItemModel):
    """
    Table model used to display Train records.
    """

    HEADERS = [
        "Number",
        "Symbol",
        "Name",
        "Type",
        "Description",
        "Origin",
        "Destination",
        "Direction",
        "Priority",
        "Max Cars",
        "Max Tonnage",
        "Operating Days",
        "Departure",
        "Arrival",
        "Status",
    ]

    TRAIN_ID_ROLE = Qt.UserRole + 1

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.trains = []

        self.setColumnCount(
            len(
                self.HEADERS
            )
        )

        self.setHorizontalHeaderLabels(
            self.HEADERS
        )

    #
    # Set trains
    #

    def set_trains(
        self,
        trains,
    ):

        self.trains = list(
            trains
            or []
        )

        self.clear()

        self.setColumnCount(
            len(
                self.HEADERS
            )
        )

        self.setHorizontalHeaderLabels(
            self.HEADERS
        )

        for train in self.trains:

            status = (
                "Active"
                if train.active
                else "Inactive"
            )

            values = [
                train.number or "",
                train.symbol or "",
                train.name or "",
                train.train_type or "",
                train.description or "",
                train.origin or "",
                train.destination or "",
                train.direction or "",
                (
                    train.priority
                    if train.priority is not None
                    else ""
                ),
                (
                    train.maximum_cars
                    if train.maximum_cars is not None
                    else ""
                ),
                (
                    train.maximum_tonnage
                    if train.maximum_tonnage is not None
                    else ""
                ),
                train.operating_days or "",
                self.format_time(
                    train.scheduled_departure
                ),
                self.format_time(
                    train.scheduled_arrival
                ),
                status,
            ]

            sort_values = [
                natural_sort_key(
                    train.number
                ),
                natural_sort_key(
                    train.symbol
                ),
                str(
                    train.name
                    or ""
                ).casefold(),
                str(
                    train.train_type
                    or ""
                ).casefold(),
                str(
                    train.description
                    or ""
                ).casefold(),
                str(
                    train.origin
                    or ""
                ).casefold(),
                str(
                    train.destination
                    or ""
                ).casefold(),
                str(
                    train.direction
                    or ""
                ).casefold(),
                (
                    train.priority
                    if train.priority is not None
                    else -1
                ),
                (
                    train.maximum_cars
                    if train.maximum_cars is not None
                    else -1
                ),
                (
                    train.maximum_tonnage
                    if train.maximum_tonnage is not None
                    else -1
                ),
                str(
                    train.operating_days
                    or ""
                ).casefold(),
                self.time_sort_value(
                    train.scheduled_departure
                ),
                self.time_sort_value(
                    train.scheduled_arrival
                ),
                (
                    1
                    if train.active
                    else 0
                ),
            ]

            items = []

            for value, sort_value in zip(
                values,
                sort_values,
            ):

                item = SortableStandardItem(
                    value,
                    sort_value,
                )

                item.setEditable(
                    False
                )

                item.setData(
                    train.id,
                    self.TRAIN_ID_ROLE,
                )

                items.append(
                    item
                )

            self.appendRow(
                items
            )

    @staticmethod
    def format_time(
        value,
    ):

        if value is None:

            return ""

        return value.strftime(
            "%I:%M %p"
        ).lstrip(
            "0"
        )

    @staticmethod
    def time_sort_value(
        value,
    ):

        if value is None:

            return -1

        return (
            value.hour * 3600
            + value.minute * 60
            + value.second
        )

    #
    # Get Train
    #

    def get_train(
        self,
        row,
    ):

        if row < 0:

            return None

        if row >= self.rowCount():

            return None

        first_item = self.item(
            row,
            0,
        )

        if first_item is None:

            return None

        train_id = first_item.data(
            self.TRAIN_ID_ROLE
        )

        return next(
            (
                train
                for train in self.trains
                if train.id == train_id
            ),
            None,
        )

    def row_for_train_id(
        self,
        train_id,
    ):

        for row in range(
            self.rowCount()
        ):

            item = self.item(
                row,
                0,
            )

            if (
                item is not None
                and item.data(
                    self.TRAIN_ID_ROLE
                )
                == train_id
            ):

                return row

        return -1

    #
    # Get Train ID
    #

    def get_train_id(
        self,
        row,
    ):

        train = self.get_train(
            row
        )

        if train is None:

            return None

        return train.id
    