from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableView,
    QHBoxLayout,
    QAbstractItemView,
    QHeaderView,
)

from modelrailroadops.ui.models.car_location_table_model import (
    CarLocationTableModel
)

from modelrailroadops.ui.dialogs.assign_car_dialog import (
    AssignCarDialog
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE
)


class CarLocationsWidget(QWidget):
    """
    Displays current car locations:
    Car -> Industry -> Track -> Spot
    """

    def __init__(self, parent=None):

        super().__init__(parent)


        self.model = CarLocationTableModel()


        self.table = QTableView()


        self.table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )


        self.table.setModel(
            self.model
        )


        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )


        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )


        self.table.setAlternatingRowColors(
            True
        )


        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )


        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )


        self.table.horizontalHeader().setStretchLastSection(
            True
        )


        self.table.verticalHeader().setVisible(
            False
        )



        self.assign_button = QPushButton(
            "Assign Car"
        )


        self.move_button = QPushButton(
            "Move Car"
        )


        self.clear_button = QPushButton(
            "Clear Location"
        )


        self.refresh_button = QPushButton(
            "Refresh"
        )



        button_layout = QHBoxLayout()


        button_layout.addWidget(
            self.assign_button
        )


        button_layout.addWidget(
            self.move_button
        )


        button_layout.addWidget(
            self.clear_button
        )


        button_layout.addWidget(
            self.refresh_button
        )


        button_layout.addStretch()



        layout = QVBoxLayout(self)


        layout.addWidget(
            self.table
        )


        layout.addLayout(
            button_layout
        )



        self.assign_button.clicked.connect(
            self.assign_car
        )


        self.refresh_button.clicked.connect(
            self.refresh
        )


        self.refresh()



    def refresh(self):
        """
        Reload car location data.
        """

        self.model.load_data()

        self.table.resizeColumnsToContents()



    def assign_car(self):
        """
        Open assign car dialog.
        """

        dialog = AssignCarDialog(
            self
        )


        if dialog.exec():

            self.refresh()