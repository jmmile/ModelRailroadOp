from PySide6.QtCore import (
    Qt,
)

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
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

from modelrailroadops.services.switch_list_move_service import (
    SwitchListMoveService,
)

from modelrailroadops.ui.models.switch_list_table_model import (
    SwitchListTableModel,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)

from modelrailroadops.ui.switch_list.switch_list_preview_dialog import (
    SwitchListPreviewDialog,
)


class SwitchListWidget(QWidget):
    """
    Displays the switch list for a selected
    Operations Session.

    The widget loads active and in-progress Waybills
    assigned to the selected Operations Session.

    The user can preview, print, and complete
    switch-list moves.
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

        #
        # Preview / Print button
        #

        self.preview_button = QPushButton(
            "Preview / Print"
        )

        self.preview_button.setEnabled(
            False
        )

        session_layout.addWidget(
            self.preview_button
        )

        #
        # Complete Move button
        #

        self.complete_move_button = QPushButton(
            "Complete Move"
        )

        self.complete_move_button.setEnabled(
            False
        )

        session_layout.addWidget(
            self.complete_move_button
        )

        #
        # Refresh button
        #

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

        self.preview_button.clicked.connect(
            self.preview_switch_list
        )

        self.complete_move_button.clicked.connect(
            self.complete_selected_move
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.session_combo.currentIndexChanged.connect(
            self.session_changed
        )

        self.table.selectionModel().selectionChanged.connect(
            self.selection_changed
        )

        #
        # Initial load
        #

        self.load_operations_sessions()

    #
    # Load Operations Sessions
    #

    def load_operations_sessions(
        self,
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
            None,
        )

        with SessionLocal() as session:

            statement = (
                select(
                    OperationsSession
                )
                .order_by(
                    OperationsSession.session_date.desc(),
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
                    or (
                        f"Session "
                        f"{operations_session.id}"
                    )
                )

                display_name = (
                    f"{name} "
                    f"({operations_session.session_date})"
                )

                self.session_combo.addItem(
                    display_name,
                    operations_session.id,
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

            self.preview_button.setEnabled(
                False
            )

            self.complete_move_button.setEnabled(
                False
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
        index,
    ):

        operations_session_id = (
            self.session_combo.currentData()
        )

        if operations_session_id is None:

            self.model.set_operations_session(
                None
            )

            self.preview_button.setEnabled(
                False
            )

            self.complete_move_button.setEnabled(
                False
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
        self,
    ):

        operations_session_id = (
            self.session_combo.currentData()
        )

        if operations_session_id is None:

            self.model.set_operations_session(
                None
            )

            self.preview_button.setEnabled(
                False
            )

            self.complete_move_button.setEnabled(
                False
            )

            self.status_label.setText(
                "Select an Operations Session."
            )

            return

        self.model.set_operations_session(
            operations_session_id
        )

        #
        # Start the table sorted by the route sequence
        # where the train will set out each car.
        #

        self.table.sortByColumn(
            2,
            Qt.AscendingOrder,
        )

        self.table.horizontalHeader().setSortIndicator(
            2,
            Qt.AscendingOrder,
        )

        self.table.resizeColumnsToContents()

        count = (
            self.model.rowCount()
        )

        self.preview_button.setEnabled(
            True
        )

        self.complete_move_button.setEnabled(
            False
        )

        self.status_label.setText(
            f"{count} switch list moves"
        )

    #
    # Table selection changed
    #

    def selection_changed(
        self,
        selected,
        deselected,
    ):

        has_selection = (
            self.table.currentIndex().isValid()
        )

        has_rows = (
            self.model.rowCount() > 0
        )

        self.complete_move_button.setEnabled(
            has_selection
            and has_rows
        )

    #
    # Get selected Waybill ID
    #

    def get_selected_waybill_id(
        self,
    ):

        index = (
            self.table.currentIndex()
        )

        if not index.isValid():

            return None

        return self.model.get_waybill_id(
            index.row()
        )

    #
    # Complete selected move
    #

    def complete_selected_move(
        self,
    ):

        waybill_id = (
            self.get_selected_waybill_id()
        )

        if waybill_id is None:

            QMessageBox.warning(
                self,
                "No Move Selected",
                "Please select a switch-list move first.",
            )

            return

        #
        # Validate the move before asking
        # the user for confirmation.
        #

        can_complete, message = (
            SwitchListMoveService.can_complete_move(
                waybill_id
            )
        )

        if not can_complete:

            QMessageBox.warning(
                self,
                "Move Cannot Be Completed",
                message,
            )

            return

        #
        # Get selected row information for
        # the confirmation message.
        #

        index = (
            self.table.currentIndex()
        )

        row = self.model.get_row(
            index.row()
        )

        if row is None:

            return

        car_name = (
            row.get(
                "car",
                "",
            )
            or ""
        )

        destination = (
            row.get(
                "destination",
                "",
            )
            or ""
        )

        destination_track = (
            row.get(
                "destination_track",
                "",
            )
            or ""
        )

        destination_spot = (
            row.get(
                "destination_spot",
                "",
            )
            or ""
        )

        confirmation_text = (
            f"Complete the move for {car_name}?\n\n"
            f"Destination: {destination}"
        )

        if destination_track:

            confirmation_text += (
                f"\nTrack: {destination_track}"
            )

        if destination_spot:

            confirmation_text += (
                f"\nSpot: {destination_spot}"
            )

        confirmation_text += (
            "\n\n"
            "The car will be moved to the destination "
            "spot and the Waybill will be marked "
            "COMPLETED."
        )

        answer = QMessageBox.question(
            self,
            "Complete Move",
            confirmation_text,
            (
                QMessageBox.Yes
                | QMessageBox.No
            ),
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        #
        # Complete the move.
        #

        success, result_message = (
            SwitchListMoveService.complete_move(
                waybill_id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Move Failed",
                result_message,
            )

            self.refresh()

            return

        #
        # Refresh the switch list.
        #

        self.refresh()

        QMessageBox.information(
            self,
            "Move Completed",
            result_message,
        )

    #
    # Preview / Print Switch List
    #

    def preview_switch_list(
        self,
    ):

        operations_session_id = (
            self.session_combo.currentData()
        )

        if operations_session_id is None:

            return

        session_name = (
            self.session_combo.currentText()
        )

        session_date = None

        #
        # Get the actual Operations Session
        # so the preview receives the real
        # operating date.
        #

        with SessionLocal() as session:

            operations_session = session.get(
                OperationsSession,
                operations_session_id,
            )

            if operations_session is not None:

                session_name = (
                    operations_session.name
                    or (
                        f"Session "
                        f"{operations_session.id}"
                    )
                )

                session_date = (
                    operations_session.session_date
                )

        dialog = SwitchListPreviewDialog(
            operations_session_id=(
                operations_session_id
            ),
            session_name=session_name,
            session_date=session_date,
            parent=self,
        )

        dialog.exec()

    #
    # Refresh
    #

    def refresh(
        self,
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

        self.preview_button.setEnabled(
            False
        )

        self.complete_move_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Select an Operations Session."
        )

    #
    # Show event
    #

    def showEvent(
        self,
        event,
    ):

        super().showEvent(
            event
        )

        self.refresh()
