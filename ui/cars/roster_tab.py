from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QComboBox,
    QTableView
)

from PySide6.QtCore import Qt

from ui.cars.car_table_model import CarTableModel


class RosterTab(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("Search"))

        self.search = QLineEdit()

        toolbar.addWidget(self.search)

        toolbar.addWidget(QLabel("Status"))

        self.status = QComboBox()

        self.status.addItems([
            "All",
            "Loaded",
            "Empty",
            "Bad Order"
        ])

        toolbar.addWidget(self.status)

        toolbar.addStretch()

        self.addButton = QPushButton("Add Car")

        toolbar.addWidget(self.addButton)

        layout.addLayout(toolbar)

        self.table = QTableView()

        self.model = CarTableModel()

        self.table.setModel(self.model)

        self.table.setSortingEnabled(True)

        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.table)