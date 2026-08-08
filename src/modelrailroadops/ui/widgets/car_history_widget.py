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
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car import Car

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