from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
)


class OperationsSessionTableModel(
    QAbstractTableModel
):
    HEADERS = [
        "Session #",
        "Session",
        "Date",
        "Status",
        "Notes",
    ]

    def __init__(
        self,
        sessions=None,
    ):

        super().__init__()

        self.sessions = (
            sessions
            if sessions is not None
            else []
        )

    def rowCount(
        self,
        parent=QModelIndex(),
    ):

        if parent.isValid():

            return 0

        return len(
            self.sessions
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
            or row >= len(self.sessions)
        ):

            return None

        operations_session = (
            self.sessions[row]
        )

        if role == Qt.DisplayRole:

            if column == 0:

                return (
                    operations_session.id
                )

            if column == 1:

                return (
                    operations_session.name
                )

            if column == 2:

                if (
                    operations_session.session_date
                    is None
                ):

                    return ""

                return (
                    operations_session
                    .session_date
                    .strftime(
                        "%Y-%m-%d"
                    )
                )

            if column == 3:

                return (
                    operations_session.status
                )

            if column == 4:

                return (
                    operations_session.notes
                    or ""
                )

        if role == Qt.TextAlignmentRole:

            if column == 0:

                return Qt.AlignCenter

            if column == 2:

                return Qt.AlignCenter

            if column == 3:

                return Qt.AlignCenter

        return None

    def set_sessions(
        self,
        sessions,
    ):

        self.beginResetModel()

        self.sessions = (
            sessions
            if sessions is not None
            else []
        )

        self.endResetModel()

    def get_session(
        self,
        row,
    ):

        if row < 0:

            return None

        if row >= len(
            self.sessions
        ):

            return None

        return self.sessions[
            row
        ]