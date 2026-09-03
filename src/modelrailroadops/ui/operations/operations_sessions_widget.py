from PySide6.QtCore import (
    Qt,
)

from PySide6.QtGui import (
    QStandardItem,
    QStandardItemModel,
)

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.train import Train

from modelrailroadops.services.car_move_generation_service import (
    CarMoveGenerationService,
)

from modelrailroadops.services.car_move_service import (
    CarMoveService,
)

from modelrailroadops.services.locomotive_service import (
    LocomotiveService,
)

from modelrailroadops.services.operations_session_service import (
    OperationsSessionService,
)

from modelrailroadops.services.operations_session_train_service import (
    OperationsSessionTrainService,
)

from modelrailroadops.services.operations_session_train_locomotive_service import (
    OperationsSessionTrainLocomotiveService,
)

from modelrailroadops.services.train_route_service import (
    TrainRouteService,
)

from modelrailroadops.ui.dialogs.add_operations_session_dialog import (
    AddOperationsSessionDialog,
)

from modelrailroadops.ui.operations.car_move_table_model import (
    CarMoveTableModel,
)

from modelrailroadops.ui.operations.operations_session_table_model import (
    OperationsSessionTableModel,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)

from modelrailroadops.ui.trains.train_route_table_model import (
    TrainRouteTableModel,
)

from modelrailroadops.ui.waybills.waybill_preview_dialog import (
    WaybillPreviewDialog,
)

from modelrailroadops.ui.waybills.waybill_table_model import (
    WaybillTableModel,
)


class AssignTrainDialog(QDialog):

    def __init__(
        self,
        operations_session_id,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.setWindowTitle(
            "Assign Train"
        )

        self.setModal(
            True
        )

        layout = QVBoxLayout(
            self
        )

        form_layout = QFormLayout()

        self.train_combo = QComboBox()

        self.load_trains(
            operations_session_id
        )

        form_layout.addRow(
            "Train:",
            self.train_combo
        )

        layout.addLayout(
            form_layout
        )

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )

        button_box.accepted.connect(
            self.accept
        )

        button_box.rejected.connect(
            self.reject
        )

        layout.addWidget(
            button_box
        )

    def load_trains(
        self,
        operations_session_id,
    ):

        assigned = (
            OperationsSessionTrainService.get_by_operations_session(
                operations_session_id
            )
        )

        assigned_train_ids = {
            assignment.train_id
            for assignment in assigned
        }

        with SessionLocal() as session:

            statement = (
                select(
                    Train
                )
                .order_by(
                    Train.number,
                    Train.name,
                )
            )

            trains = (
                session.execute(
                    statement
                )
                .scalars()
                .all()
            )

            for train in trains:

                if train.id in assigned_train_ids:

                    continue

                display = (
                    f"{train.symbol} - "
                    f"{train.name}"
                )

                self.train_combo.addItem(
                    display,
                    train.id,
                )

    def get_train_id(
        self,
    ):

        return self.train_combo.currentData()


class AssignLocomotiveDialog(QDialog):
    """
    Dialog used to assign a locomotive to a
    Train within an Operations Session.
    """

    def __init__(
        self,
        operations_session_train_id,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.operations_session_train_id = (
            operations_session_train_id
        )

        self.setWindowTitle(
            "Assign Locomotive"
        )

        self.setModal(
            True
        )

        self.resize(
            525,
            150,
        )

        layout = QVBoxLayout(
            self
        )

        form_layout = QFormLayout()

        self.locomotive_combo = QComboBox()

        self.load_locomotives()

        form_layout.addRow(
            "Locomotive:",
            self.locomotive_combo,
        )

        layout.addLayout(
            form_layout
        )

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )

        button_box.accepted.connect(
            self.accept
        )

        button_box.rejected.connect(
            self.reject
        )

        layout.addWidget(
            button_box
        )

    def load_locomotives(
        self,
    ):

        existing_assignments = (
            OperationsSessionTrainLocomotiveService
            .get_by_operations_session_train(
                self.operations_session_train_id
            )
        )

        assigned_locomotive_ids = {
            assignment.locomotive_id
            for assignment in existing_assignments
        }

        locomotives = (
            LocomotiveService.get_all()
        )

        for locomotive in locomotives:

            if locomotive.id in assigned_locomotive_ids:

                continue

            display_parts = [
                (
                    f"{locomotive.reporting_mark} "
                    f"{locomotive.number}"
                )
            ]

            if locomotive.model:

                display_parts.append(
                    locomotive.model
                )

            if locomotive.locomotive_type:

                display_parts.append(
                    locomotive.locomotive_type
                )

            if locomotive.horsepower is not None:

                display_parts.append(
                    f"{locomotive.horsepower} HP"
                )

            display = " - ".join(
                display_parts
            )

            self.locomotive_combo.addItem(
                display,
                locomotive.id,
            )

    def get_locomotive_id(
        self,
    ):

        return self.locomotive_combo.currentData()


class OperationsSessionsWidget(QWidget):

    ASSIGNMENT_ID_ROLE = 32
    TRAIN_ID_ROLE = 33
    LOCOMOTIVE_ASSIGNMENT_ID_ROLE = 34
    LOCOMOTIVE_ID_ROLE = 35

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

        button_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "Add Session"
        )

        self.edit_button = QPushButton(
            "Edit Session"
        )

        self.start_button = QPushButton(
            "Start Session"
        )

        self.complete_button = QPushButton(
            "Complete Session"
        )

        self.cancel_button = QPushButton(
            "Cancel Session"
        )

        self.delete_button = QPushButton(
            "Delete Session"
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        button_layout.addWidget(
            self.add_button
        )

        button_layout.addWidget(
            self.edit_button
        )

        button_layout.addWidget(
            self.start_button
        )

        button_layout.addWidget(
            self.complete_button
        )

        button_layout.addWidget(
            self.cancel_button
        )

        button_layout.addWidget(
            self.delete_button
        )

        button_layout.addWidget(
            self.refresh_button
        )

        button_layout.addStretch()

        layout.addLayout(
            button_layout
        )

        self.model = (
            OperationsSessionTableModel()
        )

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

        layout.addWidget(
            self.table
        )

        self.trains_label = QLabel(
            "Trains Assigned to Selected Session"
        )

        layout.addWidget(
            self.trains_label
        )

        train_button_layout = QHBoxLayout()

        self.add_train_button = QPushButton(
            "Add Train"
        )

        self.remove_train_button = QPushButton(
            "Remove Train"
        )

        self.refresh_trains_button = QPushButton(
            "Refresh Trains"
        )

        train_button_layout.addWidget(
            self.add_train_button
        )

        train_button_layout.addWidget(
            self.remove_train_button
        )

        train_button_layout.addWidget(
            self.refresh_trains_button
        )

        train_button_layout.addStretch()

        layout.addLayout(
            train_button_layout
        )

        self.train_table = QTableView()

        self.train_table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.train_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.train_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.train_table.setAlternatingRowColors(
            True
        )

        self.train_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.train_table.verticalHeader().setVisible(
            False
        )

        layout.addWidget(
            self.train_table
        )

        #
        # Motive Power
        #

        self.locomotives_label = QLabel(
            "Motive Power - Select an assigned train"
        )

        layout.addWidget(
            self.locomotives_label
        )

        locomotive_button_layout = QHBoxLayout()

        self.add_locomotive_button = QPushButton(
            "Add Locomotive"
        )

        self.remove_locomotive_button = QPushButton(
            "Remove Locomotive"
        )

        self.refresh_locomotives_button = QPushButton(
            "Refresh Motive Power"
        )

        locomotive_button_layout.addWidget(
            self.add_locomotive_button
        )

        locomotive_button_layout.addWidget(
            self.remove_locomotive_button
        )

        locomotive_button_layout.addWidget(
            self.refresh_locomotives_button
        )

        locomotive_button_layout.addStretch()

        layout.addLayout(
            locomotive_button_layout
        )

        self.locomotive_table = QTableView()

        self.locomotive_table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.locomotive_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.locomotive_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.locomotive_table.setAlternatingRowColors(
            True
        )

        self.locomotive_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.locomotive_table.verticalHeader().setVisible(
            False
        )

        layout.addWidget(
            self.locomotive_table
        )

        self.locomotive_table_model_data = []

        self.update_locomotive_table()

        #
        # Route
        #

        self.route_label = QLabel(
            "Route - Select an assigned train"
        )

        layout.addWidget(
            self.route_label
        )

        self.route_model = (
            TrainRouteTableModel()
        )

        self.route_table = QTableView()

        self.route_table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.route_table.setModel(
            self.route_model
        )

        self.route_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.route_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.route_table.setAlternatingRowColors(
            True
        )

        self.route_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.route_table.setSortingEnabled(
            False
        )

        self.route_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.route_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.route_table.verticalHeader().setVisible(
            False
        )

        layout.addWidget(
            self.route_table
        )

        self.waybills_label = QLabel(
            "Waybills for Selected Session"
        )

        layout.addWidget(
            self.waybills_label
        )

        self.waybill_model = (
            WaybillTableModel()
        )

        self.waybill_table = QTableView()

        self.waybill_table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.waybill_table.setModel(
            self.waybill_model
        )

        self.waybill_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.waybill_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.waybill_table.setAlternatingRowColors(
            True
        )

        self.waybill_table.setSortingEnabled(
            False
        )

        self.waybill_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.waybill_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.waybill_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.waybill_table.verticalHeader().setVisible(
            False
        )

        layout.addWidget(
            self.waybill_table
        )

        self.car_moves_label = QLabel(
            "Car Moves for Selected Session"
        )

        layout.addWidget(
            self.car_moves_label
        )

        car_move_button_layout = QHBoxLayout()

        self.generate_car_moves_button = QPushButton(
            "Generate Car Moves"
        )

        self.refresh_car_moves_button = QPushButton(
            "Refresh Car Moves"
        )

        self.delete_car_moves_button = QPushButton(
            "Delete Car Moves"
        )

        car_move_button_layout.addWidget(
            self.generate_car_moves_button
        )

        car_move_button_layout.addWidget(
            self.refresh_car_moves_button
        )

        car_move_button_layout.addWidget(
            self.delete_car_moves_button
        )

        car_move_button_layout.addStretch()

        layout.addLayout(
            car_move_button_layout
        )

        self.car_move_model = (
            CarMoveTableModel()
        )

        self.car_move_table = QTableView()

        self.car_move_table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.car_move_table.setModel(
            self.car_move_model
        )

        self.car_move_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.car_move_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.car_move_table.setAlternatingRowColors(
            True
        )

        self.car_move_table.setSortingEnabled(
            False
        )

        self.car_move_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.car_move_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.car_move_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.car_move_table.verticalHeader().setVisible(
            False
        )

        layout.addWidget(
            self.car_move_table
        )

        self.add_button.clicked.connect(
            self.add_session
        )

        self.edit_button.clicked.connect(
            self.edit_session
        )

        self.start_button.clicked.connect(
            self.start_session
        )

        self.complete_button.clicked.connect(
            self.complete_session
        )

        self.cancel_button.clicked.connect(
            self.cancel_session
        )

        self.delete_button.clicked.connect(
            self.delete_session
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.add_train_button.clicked.connect(
            self.add_train
        )

        self.remove_train_button.clicked.connect(
            self.remove_train
        )

        self.refresh_trains_button.clicked.connect(
            self.refresh_trains
        )

        self.add_locomotive_button.clicked.connect(
            self.add_locomotive
        )

        self.remove_locomotive_button.clicked.connect(
            self.remove_locomotive
        )

        self.refresh_locomotives_button.clicked.connect(
            self.refresh_locomotives
        )

        self.generate_car_moves_button.clicked.connect(
            self.generate_car_moves
        )

        self.refresh_car_moves_button.clicked.connect(
            self.refresh_car_moves
        )

        self.delete_car_moves_button.clicked.connect(
            self.delete_car_moves
        )

        self.table.doubleClicked.connect(
            self.edit_session
        )

        self.table.selectionModel().selectionChanged.connect(
            self.session_selection_changed
        )

        self.waybill_table.doubleClicked.connect(
            self.preview_waybill
        )

        self.train_table_model_data = []

        self.refresh()

    def refresh(
        self,
    ):

        sessions = (
            OperationsSessionService.get_all()
        )

        self.model.set_sessions(
            sessions
        )

        self.table.resizeColumnsToContents()

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if indexes:

            operations_session = (
                self.model.get_session(
                    indexes[0].row()
                )
            )

            self.load_trains_for_session(
                operations_session
            )

            self.load_waybills_for_session(
                operations_session
            )

            self.load_car_moves_for_session(
                operations_session
            )

        else:

            self.clear_trains()
            self.clear_waybills()
            self.clear_car_moves()

    def session_selection_changed(
        self,
        selected,
        deselected,
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            self.clear_trains()
            self.clear_waybills()
            self.clear_car_moves()

            return

        operations_session = (
            self.model.get_session(
                indexes[0].row()
            )
        )

        self.load_trains_for_session(
            operations_session
        )

        self.load_waybills_for_session(
            operations_session
        )

        self.load_car_moves_for_session(
            operations_session
        )

    def load_trains_for_session(
        self,
        operations_session,
    ):

        if operations_session is None:

            self.clear_trains()

            return

        assignments = (
            OperationsSessionTrainService.get_by_operations_session(
                operations_session.id
            )
        )

        self.train_table_model_data = []

        for assignment in assignments:

            train = self.get_train(
                assignment.train_id
            )

            if train is None:

                continue

            self.train_table_model_data.append(
                (
                    assignment.id,
                    train.id,
                    train.symbol,
                    train.name,
                    getattr(
                        train,
                        "origin",
                        None,
                    ),
                    getattr(
                        train,
                        "destination",
                        None,
                    ),
                    getattr(
                        train,
                        "direction",
                        None,
                    ),
                )
            )

        self.update_train_table()

        self.clear_route()
        self.clear_locomotives()

    def get_train(
        self,
        train_id,
    ):

        if train_id is None:

            return None

        with SessionLocal() as session:

            return session.get(
                Train,
                train_id,
            )

    def update_train_table(
        self,
    ):

        model = QStandardItemModel(
            self
        )

        model.setHorizontalHeaderLabels(
            [
                "Symbol",
                "Name",
                "Origin",
                "Destination",
                "Direction",
            ]
        )

        for (
            assignment_id,
            train_id,
            number,
            name,
            origin,
            destination,
            direction,
        ) in self.train_table_model_data:

            items = [
                QStandardItem(
                    number or ""
                ),
                QStandardItem(
                    name or ""
                ),
                QStandardItem(
                    origin or ""
                ),
                QStandardItem(
                    destination or ""
                ),
                QStandardItem(
                    direction or ""
                ),
            ]

            items[0].setData(
                assignment_id,
                self.ASSIGNMENT_ID_ROLE,
            )

            items[0].setData(
                train_id,
                self.TRAIN_ID_ROLE,
            )

            model.appendRow(
                items
            )

        self.train_table.setModel(
            model
        )

        self.train_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.train_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.train_table.selectionModel().selectionChanged.connect(
            self.train_selection_changed
        )

    def train_selection_changed(
        self,
        selected,
        deselected,
    ):

        train_id = (
            self.get_selected_train_id()
        )

        assignment_id = (
            self.get_selected_train_assignment_id_without_message()
        )

        if train_id is None:

            self.clear_route()
            self.clear_locomotives()

            return

        self.load_route_for_train(
            train_id
        )

        self.load_locomotives_for_train_assignment(
            assignment_id
        )

    def get_selected_train_id(
        self,
    ):

        selection_model = (
            self.train_table.selectionModel()
        )

        if selection_model is None:

            return None

        indexes = (
            selection_model.selectedRows()
        )

        if not indexes:

            return None

        return indexes[0].data(
            self.TRAIN_ID_ROLE
        )

    def get_selected_train_assignment_id_without_message(
        self,
    ):

        selection_model = (
            self.train_table.selectionModel()
        )

        if selection_model is None:

            return None

        indexes = (
            selection_model.selectedRows()
        )

        if not indexes:

            return None

        return indexes[0].data(
            self.ASSIGNMENT_ID_ROLE
        )

    #
    # Motive Power
    #

    def load_locomotives_for_train_assignment(
        self,
        assignment_id,
    ):

        if assignment_id is None:

            self.clear_locomotives()

            return

        assignments = (
            OperationsSessionTrainLocomotiveService
            .get_by_operations_session_train(
                assignment_id
            )
        )

        self.locomotive_table_model_data = []

        for assignment in assignments:

            locomotive = assignment.locomotive

            if locomotive is None:

                continue

            self.locomotive_table_model_data.append(
                (
                    assignment.id,
                    locomotive.id,
                    assignment.sequence,
                    locomotive.reporting_mark,
                    locomotive.number,
                    locomotive.model,
                    locomotive.locomotive_type,
                    locomotive.horsepower,
                )
            )

        self.update_locomotive_table()

        train_id = (
            self.get_selected_train_id()
        )

        train = self.get_train(
            train_id
        )

        if train is None:

            self.locomotives_label.setText(
                "Motive Power - Select an assigned train"
            )

            return

        self.locomotives_label.setText(
            (
                f"Motive Power - "
                f"{train.symbol or ''} - "
                f"{train.name or ''}"
            )
        )

    def update_locomotive_table(
        self,
    ):

        model = QStandardItemModel(
            self
        )

        model.setHorizontalHeaderLabels(
            [
                "Seq",
                "Reporting Mark",
                "Number",
                "Model",
                "Type",
                "Horsepower",
            ]
        )

        for (
            assignment_id,
            locomotive_id,
            sequence,
            reporting_mark,
            number,
            model_name,
            locomotive_type,
            horsepower,
        ) in self.locomotive_table_model_data:

            items = [
                QStandardItem(
                    str(sequence)
                ),
                QStandardItem(
                    reporting_mark or ""
                ),
                QStandardItem(
                    number or ""
                ),
                QStandardItem(
                    model_name or ""
                ),
                QStandardItem(
                    locomotive_type or ""
                ),
                QStandardItem(
                    (
                        str(horsepower)
                        if horsepower is not None
                        else ""
                    )
                ),
            ]

            items[0].setData(
                assignment_id,
                self.LOCOMOTIVE_ASSIGNMENT_ID_ROLE,
            )

            items[0].setData(
                locomotive_id,
                self.LOCOMOTIVE_ID_ROLE,
            )

            model.appendRow(
                items
            )

        self.locomotive_table.setModel(
            model
        )

        self.locomotive_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.locomotive_table.horizontalHeader().setStretchLastSection(
            True
        )

    def clear_locomotives(
        self,
    ):

        self.locomotive_table_model_data = []

        self.update_locomotive_table()

        self.locomotives_label.setText(
            "Motive Power - Select an assigned train"
        )

    def refresh_locomotives(
        self,
    ):

        assignment_id = (
            self.get_selected_train_assignment_id_without_message()
        )

        if assignment_id is None:

            self.clear_locomotives()

            return

        self.load_locomotives_for_train_assignment(
            assignment_id
        )

    def add_locomotive(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        if operations_session.status == "COMPLETED":

            QMessageBox.warning(
                self,
                "Assign Locomotive",
                (
                    "A completed Operations Session "
                    "cannot be changed."
                ),
            )

            return

        if operations_session.status == "CANCELLED":

            QMessageBox.warning(
                self,
                "Assign Locomotive",
                (
                    "A cancelled Operations Session "
                    "cannot be changed."
                ),
            )

            return

        assignment_id = (
            self.get_selected_train_assignment_id()
        )

        if assignment_id is None:

            return

        dialog = AssignLocomotiveDialog(
            assignment_id,
            self,
        )

        if (
            dialog.exec()
            != QDialog.Accepted
        ):

            return

        locomotive_id = (
            dialog.get_locomotive_id()
        )

        if locomotive_id is None:

            QMessageBox.warning(
                self,
                "Assign Locomotive",
                (
                    "There are no available locomotives "
                    "to assign."
                ),
            )

            return

        success, result = (
            OperationsSessionTrainLocomotiveService.create(
                assignment_id,
                locomotive_id,
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Assign Locomotive",
                str(result),
            )

            return

        self.load_locomotives_for_train_assignment(
            assignment_id
        )

    def get_selected_locomotive_assignment_id(
        self,
    ):

        selection_model = (
            self.locomotive_table.selectionModel()
        )

        if selection_model is None:

            return None

        indexes = (
            selection_model.selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Locomotive Assignment",
                "Please select a locomotive.",
            )

            return None

        return indexes[0].data(
            self.LOCOMOTIVE_ASSIGNMENT_ID_ROLE
        )

    def remove_locomotive(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        if operations_session.status == "COMPLETED":

            QMessageBox.warning(
                self,
                "Remove Locomotive",
                (
                    "A completed Operations Session "
                    "cannot be changed."
                ),
            )

            return

        if operations_session.status == "CANCELLED":

            QMessageBox.warning(
                self,
                "Remove Locomotive",
                (
                    "A cancelled Operations Session "
                    "cannot be changed."
                ),
            )

            return

        assignment_id = (
            self.get_selected_train_assignment_id()
        )

        if assignment_id is None:

            return

        locomotive_assignment_id = (
            self.get_selected_locomotive_assignment_id()
        )

        if locomotive_assignment_id is None:

            return

        answer = QMessageBox.question(
            self,
            "Remove Locomotive",
            (
                "Remove the selected locomotive "
                "from this train?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        success, result = (
            OperationsSessionTrainLocomotiveService.delete(
                locomotive_assignment_id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Remove Locomotive",
                str(result),
            )

            return

        self.load_locomotives_for_train_assignment(
            assignment_id
        )

    #
    # Route
    #

    def load_route_for_train(
        self,
        train_id,
    ):

        if train_id is None:

            self.clear_route()

            return

        routes = (
            TrainRouteService.get_by_train(
                train_id
            )
        )

        self.route_model.set_routes(
            routes
        )

        self.route_table.resizeColumnsToContents()

        train = self.get_train(
            train_id
        )

        if train is None:

            self.route_label.setText(
                "Route"
            )

            return

        number = (
            train.symbol
            or ""
        )

        name = (
            train.name
            or ""
        )

        self.route_label.setText(
            (
                f"Route - "
                f"{number} - {name}"
            )
        )

    def clear_route(
        self,
    ):

        self.route_model.set_routes(
            []
        )

        self.route_label.setText(
            "Route - Select an assigned train"
        )

    def clear_trains(
        self,
    ):

        self.train_table_model_data = []

        self.update_train_table()

        self.clear_route()
        self.clear_locomotives()

    def load_waybills_for_session(
        self,
        operations_session,
    ):

        if operations_session is None:

            self.clear_waybills()

            return

        waybills = (
            OperationsSessionService.get_waybills_by_session(
                operations_session.id
            )
        )

        self.waybill_model.set_waybills(
            waybills
        )

        self.waybill_table.resizeColumnsToContents()

    def clear_waybills(
        self,
    ):

        self.waybill_model.set_waybills(
            []
        )

    def load_car_moves_for_session(
        self,
        operations_session,
    ):

        if operations_session is None:

            self.clear_car_moves()

            return

        moves = (
            CarMoveService.get_by_operations_session(
                operations_session.id
            )
        )

        self.car_move_model.set_moves(
            moves
        )

        self.car_move_table.resizeColumnsToContents()

    def clear_car_moves(
        self,
    ):

        self.car_move_model.set_moves(
            []
        )

    def refresh_car_moves(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        self.load_car_moves_for_session(
            operations_session
        )

    def generate_car_moves(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        if operations_session.status == "COMPLETED":

            QMessageBox.warning(
                self,
                "Generate Car Moves",
                (
                    "Car Moves cannot be generated "
                    "for a completed Operations Session."
                ),
            )

            return

        if operations_session.status == "CANCELLED":

            QMessageBox.warning(
                self,
                "Generate Car Moves",
                (
                    "Car Moves cannot be generated "
                    "for a cancelled Operations Session."
                ),
            )

            return

        waybills = (
            OperationsSessionService.get_waybills_by_session(
                operations_session.id
            )
        )

        if not waybills:

            QMessageBox.information(
                self,
                "Generate Car Moves",
                (
                    "There are no Waybills assigned "
                    "to this Operations Session."
                ),
            )

            return

        assignments = (
            OperationsSessionTrainService.get_by_operations_session(
                operations_session.id
            )
        )

        if not assignments:

            QMessageBox.warning(
                self,
                "Generate Car Moves",
                (
                    "There are no trains assigned "
                    "to this Operations Session."
                ),
            )

            return

        answer = QMessageBox.question(
            self,
            "Generate Car Moves",
            (
                f"Generate Car Moves for "
                f"Operations Session "
                f"'{operations_session.name}'?\n\n"
                f"{len(waybills)} Waybill(s) will be "
                "checked against the assigned train "
                "routes.\n\n"
                "Existing Car Moves will not be duplicated."
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.Yes,
        )

        if answer != QMessageBox.Yes:

            return

        success, result = (
            CarMoveGenerationService.generate(
                operations_session.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Generate Car Moves",
                str(
                    "\n".join(
                        result.get(
                            "messages",
                            [
                                str(result)
                            ],
                        )
                    )
                ),
            )

            return

        self.load_car_moves_for_session(
            operations_session
        )

        generated = (
            result.get(
                "generated",
                0,
            )
        )

        skipped = (
            result.get(
                "skipped",
                0,
            )
        )

        messages = (
            result.get(
                "messages",
                [],
            )
        )

        summary = (
            f"Generated {generated} Car Move(s).\n"
            f"Skipped {skipped} Waybill(s)."
        )

        if messages:

            summary += (
                "\n\nDetails:\n"
                + "\n".join(
                    messages
                )
            )

        QMessageBox.information(
            self,
            "Generate Car Moves",
            summary,
        )

    def delete_car_moves(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        if operations_session.status == "COMPLETED":

            QMessageBox.warning(
                self,
                "Delete Car Moves",
                (
                    "Car Moves for a completed "
                    "Operations Session cannot be deleted."
                ),
            )

            return

        moves = (
            CarMoveService.get_by_operations_session(
                operations_session.id
            )
        )

        if not moves:

            QMessageBox.information(
                self,
                "Delete Car Moves",
                (
                    "There are no Car Moves to delete "
                    "for this Operations Session."
                ),
            )

            return

        answer = QMessageBox.question(
            self,
            "Delete Car Moves",
            (
                f"Delete all {len(moves)} Car Moves "
                f"for Operations Session "
                f"'{operations_session.name}'?\n\n"
                "This cannot be undone."
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        success, result = (
            CarMoveService.delete_by_operations_session(
                operations_session.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Delete Car Moves",
                str(result),
            )

            return

        self.load_car_moves_for_session(
            operations_session
        )

    def get_selected_train_assignment_id(
        self,
    ):

        selection_model = (
            self.train_table.selectionModel()
        )

        if selection_model is None:

            QMessageBox.information(
                self,
                "Train Assignment",
                "Please select a train assignment.",
            )

            return None

        indexes = (
            selection_model.selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Train Assignment",
                "Please select a train assignment.",
            )

            return None

        return indexes[0].data(
            self.ASSIGNMENT_ID_ROLE
        )

    def add_train(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        if operations_session.status == "COMPLETED":

            QMessageBox.warning(
                self,
                "Assign Train",
                (
                    "A completed Operations Session "
                    "cannot be changed."
                ),
            )

            return

        if operations_session.status == "CANCELLED":

            QMessageBox.warning(
                self,
                "Assign Train",
                (
                    "A cancelled Operations Session "
                    "cannot be changed."
                ),
            )

            return

        dialog = AssignTrainDialog(
            operations_session.id,
            self,
        )

        if (
            dialog.exec()
            != QDialog.Accepted
        ):

            return

        train_id = (
            dialog.get_train_id()
        )

        if train_id is None:

            QMessageBox.warning(
                self,
                "Assign Train",
                "Please select a train.",
            )

            return

        success, result = (
            OperationsSessionTrainService.create(
                operations_session.id,
                train_id,
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Assign Train",
                str(result),
            )

            return

        self.load_trains_for_session(
            operations_session
        )

    def remove_train(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        if operations_session.status == "COMPLETED":

            QMessageBox.warning(
                self,
                "Remove Train",
                (
                    "A completed Operations Session "
                    "cannot be changed."
                ),
            )

            return

        if operations_session.status == "CANCELLED":

            QMessageBox.warning(
                self,
                "Remove Train",
                (
                    "A cancelled Operations Session "
                    "cannot be changed."
                ),
            )

            return

        assignment_id = (
            self.get_selected_train_assignment_id()
        )

        if assignment_id is None:

            return

        answer = QMessageBox.question(
            self,
            "Remove Train",
            (
                "Remove the selected train from "
                "this Operations Session?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        success, result = (
            OperationsSessionTrainService.delete(
                assignment_id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Remove Train",
                str(result),
            )

            return

        self.load_trains_for_session(
            operations_session
        )

    def refresh_trains(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        self.load_trains_for_session(
            operations_session
        )

    def get_selected_session(
        self,
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Operations Session",
                "Please select an operations session.",
            )

            return None

        return self.model.get_session(
            indexes[0].row()
        )

    def get_selected_session_without_message(
        self,
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            return None

        return self.model.get_session(
            indexes[0].row()
        )

    def get_selected_waybill(
        self,
    ):

        indexes = (
            self.waybill_table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Waybill",
                "Please select a waybill.",
            )

            return None

        return self.waybill_model.get_waybill(
            indexes[0].row()
        )

    def add_session(
        self,
    ):

        dialog = AddOperationsSessionDialog(
            self
        )

        if (
            dialog.exec()
            == dialog.DialogCode.Accepted
        ):

            self.refresh()

    def edit_session(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        dialog = AddOperationsSessionDialog(
            self,
            operations_session,
        )

        if (
            dialog.exec()
            == dialog.DialogCode.Accepted
        ):

            self.refresh()

    def start_session(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        success, result = (
            OperationsSessionService.start(
                operations_session.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Start Session",
                str(result),
            )

            return

        self.refresh()

    def complete_session(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        answer = QMessageBox.question(
            self,
            "Complete Session",
            (
                f"Complete Operations Session "
                f"'{operations_session.name}'?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        success, result = (
            OperationsSessionService.complete(
                operations_session.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Complete Session",
                str(result),
            )

            return

        self.refresh()

    def cancel_session(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        answer = QMessageBox.question(
            self,
            "Cancel Session",
            (
                f"Cancel Operations Session "
                f"'{operations_session.name}'?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        success, result = (
            OperationsSessionService.cancel(
                operations_session.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Cancel Session",
                str(result),
            )

            return

        self.refresh()

    def delete_session(
        self,
    ):

        operations_session = (
            self.get_selected_session()
        )

        if operations_session is None:

            return

        if operations_session.status == "COMPLETED":

            QMessageBox.warning(
                self,
                "Delete Session",
                (
                    "A completed operations session "
                    "cannot be deleted."
                ),
            )

            return

        answer = QMessageBox.question(
            self,
            "Delete Session",
            (
                f"Delete Operations Session "
                f"'{operations_session.name}'?\n\n"
                "This cannot be undone."
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        success, result = (
            OperationsSessionService.delete(
                operations_session.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Delete Session",
                str(result),
            )

            return

        self.refresh()

    def preview_waybill(
        self,
    ):

        waybill = (
            self.get_selected_waybill()
        )

        if waybill is None:

            return

        waybill_id = waybill.id

        dialog = WaybillPreviewDialog(
            waybill,
            self,
        )

        dialog.exec()

        if not dialog.edited:

            return

        operations_session = (
            self.get_selected_session_without_message()
        )

        if operations_session is None:

            return

        self.load_waybills_for_session(
            operations_session
        )

        updated_waybill = None

        for row, item in enumerate(
            self.waybill_model.waybills
        ):

            if item.id == waybill_id:

                updated_waybill = item

                self.waybill_table.selectRow(
                    row
                )

                break

        if updated_waybill is not None:

            updated_dialog = WaybillPreviewDialog(
                updated_waybill,
                self,
            )

            updated_dialog.exec()