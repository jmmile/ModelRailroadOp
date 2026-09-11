from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor

from modelrailroadops.services.switch_list_service import (
    SwitchListService,
)


class OnTrainTableModel(QAbstractTableModel):
    """Read-only view of freight cars currently aboard trains."""

    HEADERS = (
        "Train",
        "Car",
        "Type",
        "Current Location",
        "Set-out Location",
        "Seq",
        "Set-out Status",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.operations_session_id = None
        self.train_id = None

    def rowCount(self, parent=None):
        return len(self.rows)

    def columnCount(self, parent=None):
        return len(self.HEADERS)

    def headerData(
        self,
        section,
        orientation,
        role=Qt.DisplayRole,
    ):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]

        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.rows):
            return None

        row = self.rows[index.row()]

        if role == Qt.BackgroundRole:
            return QColor(
                "#fff3cd"
                if row.get("can_setout", False)
                else "#f8d7da"
            )

        values = (
            row.get("train", ""),
            row.get("car", ""),
            row.get("car_type", ""),
            row.get("current_location", ""),
            row.get("destination", ""),
            row.get("setout_sequence"),
            row.get("setout_status", ""),
        )

        if role in (Qt.DisplayRole, Qt.UserRole):
            value = values[index.column()]

            if value is None:
                return ""

            return value if role == Qt.UserRole else str(value)

        if role == Qt.ToolTipRole and index.column() == 6:
            return row.get("setout_status", "")

        return None

    def sort(self, column, order=Qt.AscendingOrder):
        if not 0 <= column < len(self.HEADERS):
            return

        def sort_value(row):
            values = (
                row.get("train", ""),
                row.get("car", ""),
                row.get("car_type", ""),
                row.get("current_location", ""),
                row.get("destination", ""),
                row.get("setout_sequence"),
                row.get("setout_status", ""),
            )
            value = values[column]

            if column == 5:
                return value if value is not None else 999999

            return str(value or "").casefold()

        self.layoutAboutToBeChanged.emit()
        self.rows.sort(
            key=sort_value,
            reverse=order == Qt.DescendingOrder,
        )
        self.layoutChanged.emit()

    def set_context(self, operations_session_id, train_id=None):
        self.operations_session_id = operations_session_id
        self.train_id = train_id
        self.refresh()

    def refresh(self):
        self.beginResetModel()

        if self.operations_session_id is None:
            self.rows = []
        else:
            self.rows = SwitchListService.get_on_train_rows(
                self.operations_session_id,
                train_id=self.train_id,
            )

        self.endResetModel()

    def get_row(self, row):
        if row < 0 or row >= len(self.rows):
            return None

        return self.rows[row]
