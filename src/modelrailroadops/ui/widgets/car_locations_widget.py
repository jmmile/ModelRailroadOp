from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableView,
    QHBoxLayout,
)

from modelrailroadops.ui.models.car_location_table_model import (
    CarLocationTableModel
)

from modelrailroadops.ui.dialogs.assign_car_dialog import (
    AssignCarDialog
)


class CarLocationsWidget(QWidget):
    """
    Displays current car locations:
    Car -> Industry -> Track -> Spot
    """

    def __init__(self):
        super().__init__()

        self.model = CarLocationTableModel()

        self.table = QTableView()

        self.table.setModel(
            self.model
        )

        self.table.setSelectionBehavior(
            QTableView.SelectRows
        )

        self.table.setSelectionMode(
            QTableView.SingleSelection
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


        layout = QVBoxLayout()

        layout.addWidget(
            self.table
        )

        layout.addLayout(
            button_layout
        )

        self.setLayout(
            layout
        )


        # Button connections
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