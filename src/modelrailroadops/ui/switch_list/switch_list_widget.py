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
    QProgressBar,
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

from modelrailroadops.services.operations_session_service import (
    OperationsSessionService,
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
from modelrailroadops.ui.models.on_train_table_model import (
    OnTrainTableModel,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)

from modelrailroadops.ui.switch_list.switch_list_preview_dialog import (
    SwitchListPreviewDialog,
)
from modelrailroadops.ui.switch_list.completed_session_report_dialog import (
    CompletedSessionReportDialog,
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

        self.completed_report_button = QPushButton(
            "Completed Session Report"
        )
        self.completed_report_button.setEnabled(False)
        session_layout.addWidget(self.completed_report_button)

        self.check_session_data_button = QPushButton(
            "Check Session Data"
        )
        self.check_session_data_button.setEnabled(False)
        session_layout.addWidget(self.check_session_data_button)

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
        # Complete Session button
        #

        self.complete_session_button = QPushButton(
            "Complete Session"
        )

        self.complete_session_button.setEnabled(
            False
        )

        session_layout.addWidget(
            self.complete_session_button
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

        train_layout.addWidget(
            QLabel("Show:")
        )

        self.move_filter_combo = QComboBox()
        self.move_filter_combo.addItem("All Moves", "ALL")
        self.move_filter_combo.addItem("Pending", "PENDING")
        self.move_filter_combo.addItem("Cars On Train", "ON_TRAIN")
        self.move_filter_combo.addItem("Completed", "COMPLETED")
        train_layout.addWidget(self.move_filter_combo)

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

        self.progress_summary_label = QLabel(
            "Pending Pickups: 0 | Cars On Train: 0 | "
            "Pending Set-outs: 0 | Completed: 0"
        )
        layout.addWidget(self.progress_summary_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Session Progress: 0%")
        layout.addWidget(self.progress_bar)

        self.progress_warning_label = QLabel()
        self.progress_warning_label.setStyleSheet(
            "color: #a64b00; font-weight: bold;"
        )
        self.progress_warning_label.setVisible(False)
        layout.addWidget(self.progress_warning_label)

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
        # Cars currently aboard trains
        #

        self.on_train_label = QLabel(
            "Cars On Train: 0"
        )

        on_train_label_font = self.on_train_label.font()
        on_train_label_font.setBold(True)
        self.on_train_label.setFont(on_train_label_font)

        on_train_heading_layout = QHBoxLayout()
        on_train_heading_layout.addWidget(self.on_train_label)

        self.return_to_pickup_button = QPushButton(
            "Return Car to Pickup Location"
        )
        self.return_to_pickup_button.setEnabled(False)
        on_train_heading_layout.addWidget(
            self.return_to_pickup_button
        )
        on_train_heading_layout.addStretch()

        layout.addLayout(on_train_heading_layout)

        self.on_train_model = OnTrainTableModel(self)
        self.on_train_table = QTableView()
        self.on_train_table.setModel(self.on_train_model)
        self.on_train_table.setStyleSheet(TABLE_SELECTION_STYLE)
        self.on_train_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.on_train_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.on_train_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.on_train_table.setSortingEnabled(True)
        self.on_train_table.verticalHeader().setVisible(False)
        self.on_train_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.on_train_table.horizontalHeader().setStretchLastSection(
            True
        )
        self.on_train_table.setMinimumHeight(120)
        self.on_train_table.setMaximumHeight(220)

        layout.addWidget(
            self.on_train_table
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

        self.completed_report_button.clicked.connect(
            self.preview_completed_session_report
        )

        self.check_session_data_button.clicked.connect(
            self.check_selected_session_data
        )

        self.complete_move_button.clicked.connect(
            self.complete_selected_move
        )

        self.complete_session_button.clicked.connect(
            self.complete_selected_session
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

        self.move_filter_combo.currentIndexChanged.connect(
            self.move_filter_changed
        )

        self.table.selectionModel().selectionChanged.connect(
            self.selection_changed
        )

        self.on_train_table.selectionModel().selectionChanged.connect(
            self.on_train_selection_changed
        )

        self.return_to_pickup_button.clicked.connect(
            self.return_selected_car_to_pickup
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

        self.on_train_model.set_context(None)
        self.on_train_label.setText("Cars On Train: 0")
        self.return_to_pickup_button.setEnabled(False)

        self.move_filter_combo.blockSignals(True)
        self.move_filter_combo.setCurrentIndex(0)
        self.move_filter_combo.blockSignals(False)
        self.model.set_filter("ALL")
        self.progress_summary_label.setText(
            "Pending Pickups: 0 | Cars On Train: 0 | "
            "Pending Set-outs: 0 | Completed: 0"
        )
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Session Progress: 0%")
        self.progress_warning_label.clear()
        self.progress_warning_label.setVisible(False)

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

        self.completed_report_button.setEnabled(False)
        self.check_session_data_button.setEnabled(False)

        self.complete_move_button.setEnabled(
            False
        )

        self.complete_session_button.setEnabled(
            False
        )

        self.complete_session_button.setToolTip(
            ""
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

        self.refresh_on_train_table(
            operations_session_id,
            train_id,
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

    def move_filter_changed(self, index):
        filter_mode = self.move_filter_combo.itemData(index)
        self.model.set_filter(filter_mode)
        self.table.sortByColumn(1, Qt.AscendingOrder)
        self.table.resizeColumnsToContents()
        self.table.clearSelection()
        self.complete_move_button.setEnabled(False)
        self.update_status(self.train_combo.currentData())

    #
    #
    # Refresh Cars On Train
    #

    def refresh_on_train_table(
        self,
        operations_session_id,
        train_id,
    ):
        self.on_train_model.set_context(
            operations_session_id,
            train_id,
        )

        count = self.on_train_model.rowCount()
        self.on_train_label.setText(
            f"Cars On Train: {count}"
        )
        self.on_train_table.resizeColumnsToContents()
        self.on_train_table.clearSelection()
        self.return_to_pickup_button.setEnabled(False)

    def on_train_selection_changed(
        self,
        selected,
        deselected,
    ):
        self.return_to_pickup_button.setEnabled(
            self.on_train_table.currentIndex().isValid()
        )

    def return_selected_car_to_pickup(self):
        index = self.on_train_table.currentIndex()

        if not index.isValid():
            return

        row = self.on_train_model.get_row(index.row())

        if row is None:
            return

        car_name = row.get("car", "") or "this car"
        train_name = row.get("train", "") or "the selected train"
        origin = row.get("origin", "") or "its pickup location"

        answer = QMessageBox.question(
            self,
            "Return Car to Pickup Location",
            (
                f"Return {car_name} from {train_name} to {origin}?\n\n"
                "This will restore the PICKUP instruction to PENDING "
                "and the Waybill to ACTIVE."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        success, message = (
            SwitchListMoveService.return_car_to_pickup(
                row.get("car_move_id")
            )
        )

        if not success:
            QMessageBox.warning(
                self,
                "Return Car Failed",
                message,
            )
            self.refresh()
            return

        self.refresh()
        QMessageBox.information(
            self,
            "Car Returned",
            message,
        )

    #
    # Update Operations Session completion state
    #

    def update_session_completion_state(
        self,
    ):
        operations_session_id = (
            self.session_combo.currentData()
        )

        if operations_session_id is None:
            self.complete_session_button.setEnabled(
                False
            )

            self.complete_session_button.setToolTip(
                ""
            )

            return False

        can_complete, message = (
            OperationsSessionService.can_complete(
                operations_session_id
            )
        )

        self.complete_session_button.setEnabled(
            can_complete
        )

        self.complete_session_button.setToolTip(
            message or ""
        )

        return can_complete


    # Update status
    #

    def update_status(
        self,
        train_id,
    ):
        visible_count = (
            self.model.rowCount()
        )
        all_rows = self.model.all_rows
        total_count = len(all_rows)

        if train_id is None:
            status_text = (
                "Switch List Status: "
                f"{visible_count} of {total_count} moves shown - All Trains"
            )

        else:
            train_name = (
                self.train_combo.currentText()
            )

            status_text = (
                "Switch List Status: "
                f"{visible_count} of {total_count} moves shown - {train_name}"
            )

        pending_pickups = sum(
            1
            for row in all_rows
            if (
                row.get("move_type") == "PICKUP"
                and row.get("move_status") == "PENDING"
            )
        )
        pending_setouts = sum(
            1
            for row in all_rows
            if (
                row.get("move_type") == "SETOUT"
                and row.get("move_status") == "PENDING"
            )
        )
        completed_moves = sum(
            1
            for row in all_rows
            if row.get("move_status") == "COMPLETED"
        )
        onboard_count = self.on_train_model.rowCount()
        blocked_setouts = sum(
            1
            for row in self.on_train_model.rows
            if not row.get("can_setout", False)
        )
        completion_percent = (
            round(completed_moves * 100 / total_count)
            if total_count
            else 0
        )

        self.progress_summary_label.setText(
            f"Pending Pickups: {pending_pickups} | "
            f"Cars On Train: {onboard_count} | "
            f"Pending Set-outs: {pending_setouts} | "
            f"Completed: {completed_moves} of {total_count}"
        )
        self.progress_bar.setValue(completion_percent)
        self.progress_bar.setFormat(
            f"Session Progress: {completion_percent}%"
        )

        if blocked_setouts:
            self.progress_warning_label.setText(
                f"Warning: {blocked_setouts} onboard car(s) "
                "currently have a blocked set-out."
            )
            self.progress_warning_label.setVisible(True)
        else:
            self.progress_warning_label.clear()
            self.progress_warning_label.setVisible(False)

        session_ready = (
            self.update_session_completion_state()
        )

        if session_ready:
            status_text += (
                " - Ready to Complete Session"
            )

        self.status_label.setText(
            status_text
        )


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

        self.refresh_on_train_table(
            operations_session_id,
            train_id,
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

        with SessionLocal() as session:
            operations_session = session.get(
                OperationsSession,
                operations_session_id,
            )
            session_is_completed = (
                operations_session is not None
                and operations_session.status == "COMPLETED"
            )

        self.completed_report_button.setEnabled(
            session_is_completed
        )
        self.check_session_data_button.setEnabled(True)

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
    # Complete selected Operations Session
    #

    def complete_selected_session(
        self,
    ):
        operations_session_id = (
            self.session_combo.currentData()
        )

        if operations_session_id is None:
            QMessageBox.warning(
                self,
                "No Operations Session Selected",
                "Please select an Operations Session first.",
            )

            return

        can_complete, message = (
            OperationsSessionService.can_complete(
                operations_session_id
            )
        )

        if not can_complete:
            QMessageBox.warning(
                self,
                "Session Cannot Be Completed",
                message,
            )

            self.refresh()

            return

        session_name = (
            self.session_combo.currentText()
        )

        confirmation_text = (
            f"Complete {session_name}?"
            "\n\nAll required Waybill work is ready for completion."
            "\n\nThis will mark the Operations Session COMPLETED."
        )

        answer = QMessageBox.question(
            self,
            "Complete Operations Session",
            confirmation_text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        success, result = (
            OperationsSessionService.complete(
                operations_session_id
            )
        )

        if not success:
            QMessageBox.warning(
                self,
                "Session Completion Failed",
                result,
            )

            self.refresh()

            return

        self.refresh()

        QMessageBox.information(
            self,
            "Operations Session Completed",
            f"Operations Session #{operations_session_id} has been completed.",
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

    def preview_completed_session_report(self):
        operations_session_id = self.session_combo.currentData()
        if operations_session_id is None:
            return

        dialog = CompletedSessionReportDialog(
            operations_session_id=operations_session_id,
            parent=self,
        )
        dialog.exec()

    def check_selected_session_data(self):
        operations_session_id = self.session_combo.currentData()
        if operations_session_id is None:
            return

        result = SwitchListService.check_session_consistency(
            operations_session_id
        )
        if result is None:
            QMessageBox.warning(
                self,
                "Session Data Check",
                "The Operations Session could not be found.",
            )
            return

        if not result["issues"]:
            QMessageBox.information(
                self,
                "Session Data Check",
                "No session data inconsistencies were found.",
            )
            return

        issue_text = "\n".join(
            f"• {issue}" for issue in result["issues"]
        )
        if not result["can_remove_stale_pending_moves"]:
            QMessageBox.warning(
                self,
                "Session Data Inconsistencies",
                issue_text,
            )
            return

        answer = QMessageBox.question(
            self,
            "Remove Stale Pending Moves?",
            (
                f"{issue_text}\n\n"
                "This appears to be legacy session data. Remove only the "
                f"{result['pending_move_count']} stale PENDING move "
                "instruction(s)?\n\n"
                "This will not change waybills, car locations, or car history. "
                "Choose No to leave everything unchanged."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        success, message = SwitchListService.remove_stale_pending_moves(
            operations_session_id
        )
        if not success:
            QMessageBox.warning(
                self,
                "Session Cleanup Failed",
                message,
            )
            return

        self.refresh()
        QMessageBox.information(
            self,
            "Session Cleanup Complete",
            message,
        )

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
