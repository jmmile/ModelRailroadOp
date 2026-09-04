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

from modelrailroadops.services.switch_list_service import (
    SwitchListService,
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
    Displays operator-facing switch-list instructions for a
    selected Operations Session.

    Each displayed row represents one generated CarMove:

        PICKUP
        SETOUT

    The switch list may display all Trains in the Operations
    Session or be filtered to one selected Train.

    The user can preview, print, and complete individual
    switch-list instructions.
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
        # Train filter controls
        #

        train_layout = QHBoxLayout()

        train_layout.addWidget(
            QLabel(
                "Train:"
            )
        )

        self.train_combo = QComboBox()

        self.train_combo.setMinimumWidth(
            300
        )

        self.train_combo.setEnabled(
            False
        )

        self.train_combo.addItem(
            "All Trains",
            None,
        )

        train_layout.addWidget(
            self.train_combo
        )

        train_layout.addStretch()

        layout.addLayout(
            train_layout
        )

        #
        # Status
        #

        self.status_label = QLabel(
            "Switch List Status: Select an Operations Session."
        )

        status_font = self.status_label.font()

        status_font.setBold(
            True
        )

        self.status_label.setFont(
            status_font
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

        self.train_combo.currentIndexChanged.connect(
            self.train_changed
        )

        self.table.selectionModel().selectionChanged.connect(
            self.selection_changed
        )

        #
        # Initial load
        #

        self.load_operations_sessions()

    #
    # Format Operations Session display name
    #

    @staticmethod
    def get_operations_session_display_name(
        operations_session,
    ):
        if operations_session is None:
            return ""

        name = (
            operations_session.name
            or "Operations Session"
        )

        session_date = (
            operations_session.session_date
        )

        if session_date is not None:
            return (
                f"#{operations_session.id} - "
                f"{name} "
                f"({session_date})"
            )

        return (
            f"#{operations_session.id} - "
            f"{name}"
        )

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
                display_name = (
                    self.get_operations_session_display_name(
                        operations_session
                    )
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

        if current_id is None:
            self.clear_switch_list()

        else:
            self.load_switch_list()

    #
    # Clear Switch List
    #

    def clear_switch_list(
        self,
    ):
        self.model.set_train(
            None
        )

        self.model.set_operations_session(
            None
        )

        self.train_combo.blockSignals(
            True
        )

        self.train_combo.clear()

        self.train_combo.addItem(
            "All Trains",
            None,
        )

        self.train_combo.setCurrentIndex(
            0
        )

        self.train_combo.setEnabled(
            False
        )

        self.train_combo.blockSignals(
            False
        )

        self.preview_button.setEnabled(
            False
        )

        self.complete_move_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Switch List Status: Select an Operations Session."
        )

    #
    # Operations Session changed
    #

    def session_changed(
        self,
        index,
    ):
        operations_session_id = (
            self.session_combo.itemData(
                index
            )
        )

        if operations_session_id is None:
            self.clear_switch_list()
            return

        self.load_train_options(
            operations_session_id,
            selected_train_id=None,
        )

        self.load_switch_list()

    #
    # Load Train options
    #

    def load_train_options(
        self,
        operations_session_id,
        selected_train_id=None,
    ):
        """
        Populate the Train selector from the generated
        CarMoves in the selected Operations Session.

        Only Trains that currently have active switch-list
        instructions are displayed.
        """

        self.train_combo.blockSignals(
            True
        )

        self.train_combo.clear()

        self.train_combo.addItem(
            "All Trains",
            None,
        )

        if operations_session_id is None:
            self.train_combo.setEnabled(
                False
            )

            self.train_combo.blockSignals(
                False
            )

            return

        rows = (
            SwitchListService.get_switch_list_rows(
                operations_session_id
            )
        )

        trains = {}

        for row in rows:
            train_id = row.get(
                "train_id"
            )

            train_name = (
                row.get(
                    "train",
                    "",
                )
                or ""
            )

            if train_id is None:
                continue

            if train_id not in trains:
                trains[
                    train_id
                ] = (
                    train_name
                    or f"Train {train_id}"
                )

        sorted_trains = sorted(
            trains.items(),
            key=lambda item: (
                item[1].casefold(),
                item[0],
            ),
        )

        for train_id, train_name in sorted_trains:
            self.train_combo.addItem(
                train_name,
                train_id,
            )

        self.train_combo.setEnabled(
            True
        )

        if selected_train_id is not None:
            train_index = (
                self.train_combo.findData(
                    selected_train_id
                )
            )

            if train_index >= 0:
                self.train_combo.setCurrentIndex(
                    train_index
                )

            else:
                self.train_combo.setCurrentIndex(
                    0
                )

        else:
            self.train_combo.setCurrentIndex(
                0
            )

        self.train_combo.blockSignals(
            False
        )

    #
    # Train changed
    #

    def train_changed(
        self,
        index,
    ):
        """
        Apply the Train selected in the Train combo box
        directly to the switch-list table model.
        """

        operations_session_id = (
            self.session_combo.currentData()
        )

        if operations_session_id is None:
            return

        train_id = (
            self.train_combo.itemData(
                index
            )
        )

        self.model.set_train(
            train_id
        )

        self.table.sortByColumn(
            1,
            Qt.AscendingOrder,
        )

        self.table.horizontalHeader().setSortIndicator(
            1,
            Qt.AscendingOrder,
        )

        self.table.resizeColumnsToContents()

        self.table.clearSelection()

        self.complete_move_button.setEnabled(
            False
        )

        self.update_status(
            train_id
        )

    #
    # Update status
    #

    def update_status(
        self,
        train_id,
    ):
        count = (
            self.model.rowCount()
        )

        if train_id is None:
            self.status_label.setText(
                f"Switch List Status: {count} moves — All Trains"
            )

        else:
            train_name = (
                self.train_combo.currentText()
            )

            self.status_label.setText(
                f"Switch List Status: {count} moves — {train_name}"
            )

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
            self.clear_switch_list()
            return

        train_index = (
            self.train_combo.currentIndex()
        )

        train_id = (
            self.train_combo.itemData(
                train_index
            )
        )

        self.model.train_id = (
            train_id
        )

        self.model.set_operations_session(
            operations_session_id
        )

        self.table.sortByColumn(
            1,
            Qt.AscendingOrder,
        )

        self.table.horizontalHeader().setSortIndicator(
            1,
            Qt.AscendingOrder,
        )

        self.table.resizeColumnsToContents()

        self.table.clearSelection()

        self.preview_button.setEnabled(
            True
        )

        self.complete_move_button.setEnabled(
            False
        )

        self.update_status(
            train_id
        )

    #
    # Table selection changed
    #

    def selection_changed(
        self,
        selected,
        deselected,
    ):
        index = (
            self.table.currentIndex()
        )

        if not index.isValid():
            self.complete_move_button.setEnabled(
                False
            )
            return

        row = self.model.get_row(
            index.row()
        )

        if row is None:
            self.complete_move_button.setEnabled(
                False
            )
            return

        move_status = (
            row.get(
                "move_status",
                "",
            )
            or ""
        )

        self.complete_move_button.setEnabled(
            move_status == "PENDING"
        )

    #
    # Get selected CarMove ID
    #

    def get_selected_car_move_id(
        self,
    ):
        index = (
            self.table.currentIndex()
        )

        if not index.isValid():
            return None

        return self.model.get_car_move_id(
            index.row()
        )

    #
    # Complete selected move
    #

    def complete_selected_move(
        self,
    ):
        car_move_id = (
            self.get_selected_car_move_id()
        )

        if car_move_id is None:
            QMessageBox.warning(
                self,
                "No Move Selected",
                "Please select a switch-list move first.",
            )

            return

        index = (
            self.table.currentIndex()
        )

        if not index.isValid():
            return

        row = self.model.get_row(
            index.row()
        )

        if row is None:
            return

        move_type = (
            row.get(
                "move_type",
                "",
            )
            or ""
        )

        move_status = (
            row.get(
                "move_status",
                "",
            )
            or ""
        )

        if move_status != "PENDING":
            QMessageBox.information(
                self,
                "Move Already Completed",
                (
                    f"This {move_type or 'switch-list'} "
                    "instruction has already been completed."
                ),
            )

            self.refresh()

            return

        can_complete, message = (
            SwitchListMoveService.can_complete_move(
                car_move_id
            )
        )

        if not can_complete:
            QMessageBox.warning(
                self,
                "Move Cannot Be Completed",
                message,
            )

            return

        car_name = (
            row.get(
                "car",
                "",
            )
            or ""
        )

        train_name = (
            row.get(
                "train",
                "",
            )
            or ""
        )

        route_sequence = (
            row.get(
                "route_sequence"
            )
        )

        instruction_location = (
            row.get(
                "instruction_location",
                "",
            )
            or ""
        )

        confirmation_text = (
            f"Complete {move_type} for {car_name}?"
        )

        if train_name:
            confirmation_text += (
                f"\n\nTrain: {train_name}"
            )

        if route_sequence is not None:
            confirmation_text += (
                f"\nRoute Sequence: {route_sequence}"
            )

        if instruction_location:
            confirmation_text += (
                f"\nLocation: {instruction_location}"
            )

        if move_type == "PICKUP":
            confirmation_text += (
                "\n\n"
                "This will mark the PICKUP instruction "
                "COMPLETED and place the Waybill "
                "IN_PROGRESS."
            )

        elif move_type == "SETOUT":
            confirmation_text += (
                "\n\n"
                "This will move the car to its Waybill "
                "destination and mark the SETOUT "
                "instruction COMPLETED."
            )

            confirmation_text += (
                "\n"
                "If no required moves remain, the Waybill "
                "will also be marked COMPLETED."
            )

        else:
            confirmation_text += (
                "\n\n"
                "This will complete the selected "
                "switch-list instruction."
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

        success, result_message = (
            SwitchListMoveService.complete_move(
                car_move_id
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

        train_id = (
            self.train_combo.currentData()
        )

        train_name = ""

        if train_id is not None:
            train_name = (
                self.train_combo.currentText()
            )

        session_name = (
            self.session_combo.currentText()
        )

        session_date = None

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
            train_id=train_id,
            train_name=train_name,
            parent=self,
        )

        dialog.exec()

    #
    # Refresh
    #

    def refresh(
        self,
    ):
        current_session_id = (
            self.session_combo.currentData()
        )

        current_train_id = (
            self.train_combo.currentData()
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
                display_name = (
                    self.get_operations_session_display_name(
                        operations_session
                    )
                )

                self.session_combo.addItem(
                    display_name,
                    operations_session.id,
                )

        if current_session_id is not None:
            session_index = (
                self.session_combo.findData(
                    current_session_id
                )
            )

            if session_index >= 0:
                self.session_combo.setCurrentIndex(
                    session_index
                )

        self.session_combo.blockSignals(
            False
        )

        if current_session_id is None:
            self.clear_switch_list()
            return

        session_index = (
            self.session_combo.findData(
                current_session_id
            )
        )

        if session_index < 0:
            self.clear_switch_list()
            return

        self.load_train_options(
            current_session_id,
            selected_train_id=current_train_id,
        )

        self.load_switch_list()

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