from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car
from modelrailroadops.services.car_location_service import CarLocationService

from modelrailroadops.ui.models.car_history_table_model import (
    CarHistoryTableModel,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)



class CarHistoryWidget(QWidget):
    """
    Displays car movement history.
    """

    def __init__(
        self,
        parent=None
    ):

        super().__init__(parent)


        layout = QVBoxLayout(self)


        #
        # Filters
        #

        filter_layout = QHBoxLayout()


        filter_layout.addWidget(
            QLabel("Car:")
        )


        self.car_combo = QComboBox()


        filter_layout.addWidget(
            self.car_combo
        )


        self.refresh_button = QPushButton(
            "Refresh"
        )


        filter_layout.addWidget(
            self.refresh_button
        )


        self.undo_button = QPushButton(
            "Undo Last Movement"
        )


        filter_layout.addWidget(
            self.undo_button
        )


        filter_layout.addStretch()


        layout.addLayout(
            filter_layout
        )


        #
        # Table
        #

        self.table = QTableView()


        self.model = CarHistoryTableModel()


        self.table.setModel(
            self.model
        )


        #
        # Highlight Style
        #

        self.table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )


        self.table.setFocusPolicy(
            Qt.StrongFocus
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


        layout.addWidget(
            self.table
        )


        #
        # Connections
        #

        self.car_combo.currentIndexChanged.connect(
            self.apply_filter
        )


        self.refresh_button.clicked.connect(
            self.apply_filter
        )


        self.undo_button.clicked.connect(
            self.undo_last_movement
        )


        #
        # Initial Load
        #

        self.load_cars()

        self.apply_filter()



    def load_cars(self):

        self.car_combo.blockSignals(
            True
        )


        self.car_combo.clear()


        self.car_combo.addItem(
            "All Cars",
            None
        )


        with SessionLocal() as session:

            cars = (
                session.query(Car)
                .order_by(
                    Car.reporting_mark,
                    Car.number,
                )
                .all()
            )


            for car in cars:

                self.car_combo.addItem(
                    (
                        f"{car.reporting_mark} "
                        f"{car.number}"
                    ),
                    car.id
                )


        self.car_combo.blockSignals(
            False
        )



    def apply_filter(self):

        self.model.load_data(
            car_id=self.car_combo.currentData()
        )


        self.table.resizeColumnsToContents()


    def undo_last_movement(self):
        car_id = self.car_combo.currentData()

        found, result = CarLocationService.get_last_movement_summary(
            car_id=car_id,
        )

        if not found:
            QMessageBox.information(self, "Undo Last Movement", result)
            return

        if result["operations_session_id"] is not None:
            QMessageBox.warning(
                self,
                "Undo Last Movement",
                (
                    "This movement belongs to an Operations Session and "
                    "cannot be undone here. Use the Switch List workflow "
                    "to keep the move and Waybill statuses synchronized."
                ),
            )
            return

        answer = QMessageBox.question(
            self,
            "Undo Last Movement",
            (
                f"Return {result['car']} from:\n\n"
                f"{result['to_location']}\n\n"
                f"to:\n\n{result['from_location']}?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        undone, message = CarLocationService.undo_last_movement(
            car_id=car_id,
            movement_id=result["movement_id"],
        )

        if not undone:
            QMessageBox.warning(self, "Undo Last Movement", message)
            return

        self.refresh()
        QMessageBox.information(self, "Undo Last Movement", message)


    def refresh(self):
        """Reload cars and movement history when this tab is shown."""

        selected_car_id = self.car_combo.currentData()

        self.load_cars()

        if selected_car_id is not None:
            index = self.car_combo.findData(selected_car_id)

            if index >= 0:
                self.car_combo.setCurrentIndex(index)

        self.apply_filter()
