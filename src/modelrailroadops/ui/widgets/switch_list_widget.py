from PySide6.QtCore import (
    Qt,
)

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.operations_session import (
    OperationsSession,
)

from modelrailroadops.ui.models.switch_list_table_model import (
    SwitchListTableModel,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)


class SwitchListWidget(QWidget):
    """
    Displays the switch list for a selected
    Operations Session.
    """

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        layout = QVBoxLayout(
            self
        )

        #
        # Title
        #

        layout.addWidget(
            QLabel(
                "Switch List"
            )
        )

        #
        # Operations Session controls
        #

        session_layout = QHBoxLayout()

        session_layout.addWidget(
            QLabel(
                "Operations Session:"
            )
        )

        self.session_combo = QComboBox()

        self.session_combo.setMinimumWidth(
            300
        )

        session_layout.addWidget(
            self.session_combo
        )

        self.load_button = QPushButton(
            "Load Switch List"
        )

        session_layout.addWidget(
            self.load_button
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        session_layout.addWidget(
            self.refresh_button
        )

        session_layout.addStretch()

        layout.addLayout(
            session_layout
        )

        #
        # Status
        #

        self.status_label = QLabel(
            "Select an Operations Session."
        )

        layout.addWidget(
            self.status_label
        )

        #
        # Table model
        #

        self.model = SwitchListTableModel()

        #
        # Table
        #

        self.table = QTableView()

        self.table.setModel(
            self.model
        )

        self.table.setStyleSheet(
            TABLE_SELECTION_STYLE
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

        self.table.setSortingEnabled(
            True
        )

        self.table.setFocusPolicy(
            Qt.StrongFocus
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.table.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(
            self.table
        )

        #
        # Signals
        #

        self.load_button.clicked.connect(
            self.load_switch_list
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.session_combo.currentIndexChanged.connect(
            self.session_changed
        )

        #
        # Initial load
        #

        self.load_operations_sessions()

    #
    # Load Operations Sessions
    #

    def load_operations_sessions(
        self
    ):

        current_id = (
            self.session_combo.currentData()
        )

        self.session_combo.blockSignals(
            True
        )

        self.session_combo.clear()

        self.session_combo.addItem(
            "Select Operations Session",
            None
        )

        with SessionLocal() as session:

            statement = (
                select(
                    OperationsSession
                )
                .order_by(
                    OperationsSession.start_date.desc(),
                    OperationsSession.id.desc(),
                )
            )

            sessions = (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

            for operations_session in sessions:

                name = (
                    operations_session.name
                    or f"Session {operations_session.id}"
                )

                self.session_combo.addItem(
                    name,
                    operations_session.id
                )

        if current_id is not None:

            index = (
                self.session_combo.findData(
                    current_id
                )
            )

            if index >= 0:

                self.session_combo.setCurrentIndex(
                    index
                )

        self.session_combo.blockSignals(
            False
        )

        #
        # If there was no previously selected
        # session, leave the table empty.
        #

        if current_id is None:

            self.model.set_operations_session(
                None
            )

            self.status_label.setText(
                "Select an Operations Session."
            )

        else:

            self.load_switch_list()

    #
    # Operations Session changed
    #

    def session_changed(
        self,
        index
    ):

        operations_session_id = (
            self.session_combo.currentData()
        )

        if operations_session_id is None:

            self.model.set_operations_session(
                None
            )

            self.status_label.setText(
                "Select an Operations Session."
            )

            return

        self.load_switch_list()

    #
    # Load Switch List
    #

    def load_switch_list(
        self
    ):

        operations_session_id = (
            self.session_combo.currentData()
        )

        if operations_session_id is None:

            self.model.set_operations_session(
                None
            )

            self.status_label.setText(
                "Select an Operations Session."
            )

            return

        self.model.set_operations_session(
            operations_session_id
        )

        #
        # Start the table sorted by
        # Destination Track.
        #

        self.table.sortByColumn(
            6,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            6,
            Qt.AscendingOrder
        )

        self.table.resizeColumnsToContents()

        count = self.model.rowCount()

        self.status_label.setText(
            f"{count} switch list moves"
        )

    #
    # Refresh
    #

    def refresh(
        self
    ):

        current_id = (
            self.session_combo.currentData()
        )

        self.load_operations_sessions()

        if current_id is not None:

            index = (
                self.session_combo.findData(
                    current_id
                )
            )

            if index >= 0:

                self.session_combo.setCurrentIndex(
                    index
                )

                self.load_switch_list()

                return

        self.model.set_operations_session(
            None
        )

        self.status_label.setText(
            "Select an Operations Session."
        )

    #
    # Show event
    #

    def showEvent(
        self,
        event
    ):

        super().showEvent(
            event
        )

        self.refresh()