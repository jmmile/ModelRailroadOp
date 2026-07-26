from PySide6.QtCore import Qt
from PySide6.QtCore import QAbstractTableModel

import sqlite3

from config import DB_FILE


class CarTableModel(QAbstractTableModel):

    headers = [
        "Reporting",
        "Number",
        "Railroad",
        "Type",
        "Status",
        "Location"
    ]

    def __init__(self):

        super().__init__()

        self.rows = []

        self.load()

    def load(self):

        conn = sqlite3.connect(DB_FILE)

        cur = conn.cursor()

        cur.execute("""
            SELECT
                reporting_mark,
                number,
                owner,
                car_type,
                status,
                location
            FROM cars
            ORDER BY reporting_mark, number
        """)

        self.rows = cur.fetchall()

        conn.close()

    def rowCount(self, parent=None):

        return len(self.rows)

    def columnCount(self, parent=None):

        return len(self.headers)

    def data(self, index, role):

        if not index.isValid():
            return None

        if role == Qt.DisplayRole:

            return self.rows[index.row()][index.column()]

        return None

    def headerData(self, section, orientation, role):

        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:

            return self.headers[section]

        return section + 1