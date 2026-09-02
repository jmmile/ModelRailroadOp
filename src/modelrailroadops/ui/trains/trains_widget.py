
from PySide6.QtCore import (
    Qt,
)

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from modelrailroadops.services.train_service import (
    TrainService,
)

from modelrailroadops.ui.dialogs.add_train_dialog import (
    AddTrainDialog,
)

from modelrailroadops.ui.trains.train_table_model import (
    TrainTableModel,
)

from modelrailroadops.ui.trains.train_routes_widget import (
    TrainRoutesWidget,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)


class TrainsWidget(QWidget):
    """
    Widget used to display and manage Trains.

    The selected Train's route stops are displayed
    in a separate route-management area below the
    Train table.
    """

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        #
        # Main layout
        #

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            6,
            6,
            6,
            6,
        )

        layout.setSpacing(
            6
        )

        #
        # Buttons
        #

        button_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "Add Train"
        )

        self.edit_button = QPushButton(
            "Edit Train"
        )

        self.activate_button = QPushButton(
            "Activate"
        )

        self.deactivate_button = QPushButton(
            "Deactivate"
        )

        self.delete_button = QPushButton(
            "Delete Train"
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
            self.activate_button
        )

        button_layout.addWidget(
            self.deactivate_button
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

        #
        # Train table model
        #

        self.model = TrainTableModel(
            self
        )

        #
        # Train table
        #

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

        self.table.setSortingEnabled(
            True
        )

        self.table.sortByColumn(
            0,
            Qt.AscendingOrder,
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

        self.table.setMinimumHeight(
            200
        )

        #
        # Route widget
        #

        self.routes_widget = TrainRoutesWidget(
            self
        )

        self.routes_widget.route_changed.connect(
            self.refresh
        )

        self.routes_widget.setMinimumHeight(
            250
        )

        #
        # Splitter
        #

        self.splitter = QSplitter(
            Qt.Vertical,
            self,
        )

        self.splitter.setChildrenCollapsible(
            False
        )

        self.splitter.addWidget(
            self.table
        )

        self.splitter.addWidget(
            self.routes_widget
        )

        self.splitter.setStretchFactor(
            0,
            3
        )

        self.splitter.setStretchFactor(
            1,
            2
        )

        self.splitter.setSizes(
            [
                450,
                300,
            ]
        )

        layout.addWidget(
            self.splitter
        )

        #
        # Signals
        #

        self.add_button.clicked.connect(
            self.add_train
        )

        self.edit_button.clicked.connect(
            self.edit_train
        )

        self.activate_button.clicked.connect(
            self.activate_train
        )

        self.deactivate_button.clicked.connect(
            self.deactivate_train
        )

        self.delete_button.clicked.connect(
            self.delete_train
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.table.doubleClicked.connect(
            self.edit_train
        )

        self.table.selectionModel().selectionChanged.connect(
            self.selection_changed
        )

        #
        # Initial state
        #

        self.routes_widget.set_train(
            None
        )

        self.update_button_states()

        self.refresh()

    #
    # Refresh
    #

    def refresh(
        self,
    ):

        selected_train_id = (
            self.get_selected_train_id()
        )

        trains = (
            TrainService.get_all(
                include_inactive=True
            )
        )

        self.model.set_trains(
            trains
        )

        sort_column = (
            self.table.horizontalHeader().sortIndicatorSection()
        )

        if sort_column >= 0:
            self.model.sort(
                sort_column,
                self.table.horizontalHeader().sortIndicatorOrder(),
            )

        self.table.resizeColumnsToContents()

        #
        # Restore previous selection.
        #

        restored = False

        if selected_train_id is not None:
            selected_row = self.model.row_for_train_id(
                selected_train_id
            )

            if selected_row >= 0:
                self.table.selectRow(
                    selected_row
                )
                restored = True

        #
        # If no previous selection exists,
        # select the first train when available.
        #

        if (
            not restored
            and self.model.trains
        ):

            self.table.selectRow(
                0
            )

        #
        # If there are no trains,
        # clear the route widget.
        #

        if not self.model.trains:

            self.routes_widget.set_train(
                None
            )

        self.update_button_states()

    #
    # Get selected train
    #

    def get_selected_train(
        self,
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            return None

        return self.model.get_train(
            indexes[0].row()
        )

    #
    # Get selected train with message
    #

    def require_selected_train(
        self,
    ):

        train = (
            self.get_selected_train()
        )

        if train is None:

            QMessageBox.information(
                self,
                "Train",
                "Please select a train.",
            )

            return None

        return train

    #
    # Get selected train ID
    #

    def get_selected_train_id(
        self,
    ):

        train = (
            self.get_selected_train()
        )

        if train is None:

            return None

        return train.id

    #
    # Selection changed
    #

    def selection_changed(
        self,
        selected,
        deselected,
    ):

        train = (
            self.get_selected_train()
        )

        if train is None:

            self.routes_widget.set_train(
                None
            )

        else:

            self.routes_widget.set_train(
                train
            )

        self.update_button_states()

    #
    # Update button states
    #

    def update_button_states(
        self,
    ):

        train = (
            self.get_selected_train()
        )

        has_train = (
            train is not None
        )

        self.edit_button.setEnabled(
            has_train
        )

        self.delete_button.setEnabled(
            has_train
        )

        self.activate_button.setEnabled(
            (
                has_train
                and not train.active
            )
            if has_train
            else False
        )

        self.deactivate_button.setEnabled(
            (
                has_train
                and train.active
            )
            if has_train
            else False
        )

        self.refresh_button.setEnabled(
            True
        )

    #
    # Add train
    #

    def add_train(
        self,
    ):

        dialog = AddTrainDialog(
            parent=self
        )

        if (
            dialog.exec()
            == dialog.DialogCode.Accepted
        ):

            self.refresh()

    #
    # Edit train
    #

    def edit_train(
        self,
    ):

        train = (
            self.require_selected_train()
        )

        if train is None:

            return

        dialog = AddTrainDialog(
            parent=self,
            train=train,
        )

        if (
            dialog.exec()
            == dialog.DialogCode.Accepted
        ):

            self.refresh()

    #
    # Activate train
    #

    def activate_train(
        self,
    ):

        train = (
            self.require_selected_train()
        )

        if train is None:

            return

        success, result = (
            TrainService.activate(
                train.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Activate Train",
                str(
                    result
                ),
            )

            return

        self.refresh()

    #
    # Deactivate train
    #

    def deactivate_train(
        self,
    ):

        train = (
            self.require_selected_train()
        )

        if train is None:

            return

        success, result = (
            TrainService.deactivate(
                train.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Deactivate Train",
                str(
                    result
                ),
            )

            return

        self.refresh()

    #
    # Delete train
    #

    def delete_train(
        self,
    ):

        train = (
            self.require_selected_train()
        )

        if train is None:

            return

        answer = QMessageBox.question(
            self,
            "Delete Train",
            (
                f"Delete train "
                f"'{train.symbol} - {train.name}'?\n\n"
                "This will also delete its route stops "
                "and Operations Session assignments.\n\n"
                "This cannot be undone."
            ),
            (
                QMessageBox.Yes
                | QMessageBox.No
            ),
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        success, result = (
            TrainService.delete(
                train.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Delete Train",
                str(
                    result
                ),
            )

            return

        self.routes_widget.set_train(
            None
        )

        self.refresh()
