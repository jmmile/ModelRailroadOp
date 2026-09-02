from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
)


class OperationsSessionTrainTableModel(
    QAbstractTableModel
):

    HEADERS = [
        "Symbol",
        "Name",
        "Origin",
        "Destination",
        "Direction",
    ]

    def __init__(
        self,
        assignments=None,
    ):

        super().__init__()

        self.assignments = (
            assignments
            if assignments is not None
            else []
        )

    def rowCount(
        self,
        parent=QModelIndex(),
    ):

        if parent.isValid():

            return 0

        return len(
            self.assignments
        )

    def columnCount(
        self,
        parent=QModelIndex(),
    ):

        if parent.isValid():

            return 0

        return len(
            self.HEADERS
        )

    def headerData(
        self,
        section,
        orientation,
        role=Qt.DisplayRole,
    ):

        if role != Qt.DisplayRole:

            return None

        if orientation == Qt.Horizontal:

            if (
                0
                <= section
                < len(self.HEADERS)
            ):

                return self.HEADERS[
                    section
                ]

        return None

    def data(
        self,
        index,
        role=Qt.DisplayRole,
    ):

        if not index.isValid():

            return None

        row = index.row()
        column = index.column()

        if (
            row < 0
            or row >= len(self.assignments)
        ):

            return None

        assignment = (
            self.assignments[row]
        )

        train = getattr(
            assignment,
            "train",
            None,
        )

        if role == Qt.DisplayRole:

            if train is None:

                return ""

            if column == 0:

                return (
                    getattr(
                        train,
                        "number",
                        "",
                    )
                    or ""
                )

            if column == 1:

                return (
                    getattr(
                        train,
                        "name",
                        "",
                    )
                    or ""
                )

            if column == 2:

                return (
                    getattr(
                        train,
                        "origin",
                        "",
                    )
                    or ""
                )

            if column == 3:

                return (
                    getattr(
                        train,
                        "destination",
                        "",
                    )
                    or ""
                )

            if column == 4:

                return (
                    getattr(
                        train,
                        "direction",
                        "",
                    )
                    or ""
                )

        if role == Qt.TextAlignmentRole:

            if column == 4:

                return Qt.AlignCenter

        if role == Qt.UserRole:

            return assignment.id

        return None

    def set_assignments(
        self,
        assignments,
    ):

        self.beginResetModel()

        self.assignments = (
            assignments
            if assignments is not None
            else []
        )

        self.endResetModel()

    def get_assignment(
        self,
        row,
    ):

        if row < 0:

            return None

        if row >= len(
            self.assignments
        ):

            return None

        return self.assignments[row]

    def get_assignment_id(
        self,
        row,
    ):

        assignment = (
            self.get_assignment(
                row
            )
        )

        if assignment is None:

            return None

        return assignment.id
