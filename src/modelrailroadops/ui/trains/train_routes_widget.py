
from PySide6.QtCore import (
    Signal,
    Qt,
)

from PySide6.QtGui import (
    QPalette,
)

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from modelrailroadops.services.train_route_service import (
    TrainRouteService,
)

from modelrailroadops.ui.dialogs.add_train_route_dialog import (
    AddTrainRouteDialog,
)

from modelrailroadops.ui.trains.train_route_table_model import (
    TrainRouteTableModel,
)


class TrainRoutesWidget(QWidget):
    """
    Widget used to display and manage the route stops
    for a selected Train.
    """

    route_changed = Signal()

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        #
        # Train selection
        #

        self.train_id = None

        #
        # Main widget sizing
        #

        self.setMinimumHeight(
            300
        )

        self.setMinimumWidth(
            500
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
        # Selected train label
        #

        self.train_label = QLabel(
            "No train selected."
        )

        self.train_label.setMinimumHeight(
            24
        )

        layout.addWidget(
            self.train_label
        )

        #
        # Buttons
        #

        button_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "Add Stop"
        )

        self.edit_button = QPushButton(
            "Edit Stop"
        )

        self.move_up_button = QPushButton(
            "Move Up"
        )

        self.move_down_button = QPushButton(
            "Move Down"
        )

        self.delete_button = QPushButton(
            "Delete Stop"
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
            self.move_up_button
        )

        button_layout.addWidget(
            self.move_down_button
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
        # Route table model
        #

        self.model = TrainRouteTableModel(
            self
        )

        #
        # Route table
        #

        self.table = QTableView(
            self
        )

        self.table.setMinimumHeight(
            150
        )

        self.table.setMinimumWidth(
            400
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
            False
        )

        self.table.setShowGrid(
            True
        )

        self.table.setWordWrap(
            False
        )

        self.table.setTextElideMode(
            Qt.ElideNone
        )

        self.table.setFocusPolicy(
            Qt.StrongFocus
        )

        #
        # Table styling
        #

        self.table.setStyleSheet(
            """
            QTableView {
                color: #000000;
                background: #ffffff;
                alternate-background-color: #f0f0f0;
                gridline-color: #a0a0a0;
                selection-color: #000000;
                selection-background-color: #cce8ff;
                border: 1px solid #808080;
            }

            QTableView::item {
                color: #000000;
                background: #ffffff;
                padding: 4px;
            }

            QTableView::item:alternate {
                color: #000000;
                background: #f0f0f0;
            }

            QTableView::item:selected {
                color: #000000;
                background: #cce8ff;
            }

            QTableView::item:selected:active {
                color: #000000;
                background: #cce8ff;
            }

            QTableView::item:selected:!active {
                color: #000000;
                background: #cce8ff;
            }

            QHeaderView::section {
                color: #000000;
                background: #e0e0e0;
                border: 1px solid #a0a0a0;
                padding: 4px;
            }
            """
        )

        #
        # Table palette
        #

        palette = self.table.palette()

        palette.setColor(
            QPalette.Window,
            Qt.white,
        )

        palette.setColor(
            QPalette.Base,
            Qt.white,
        )

        palette.setColor(
            QPalette.AlternateBase,
            Qt.lightGray,
        )

        palette.setColor(
            QPalette.Text,
            Qt.black,
        )

        palette.setColor(
            QPalette.WindowText,
            Qt.black,
        )

        palette.setColor(
            QPalette.Highlight,
            Qt.lightGray,
        )

        palette.setColor(
            QPalette.HighlightedText,
            Qt.black,
        )

        self.table.setPalette(
            palette
        )

        #
        # Header configuration
        #

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.horizontalHeader().setVisible(
            True
        )

        self.table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        self.table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        self.table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.Stretch
        )

        self.table.verticalHeader().setDefaultSectionSize(
            28
        )

        layout.addWidget(
            self.table,
            1,
        )

        #
        # Signals
        #

        self.add_button.clicked.connect(
            self.add_route
        )

        self.edit_button.clicked.connect(
            self.edit_route
        )

        self.move_up_button.clicked.connect(
            self.move_up
        )

        self.move_down_button.clicked.connect(
            self.move_down
        )

        self.delete_button.clicked.connect(
            self.delete_route
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.table.doubleClicked.connect(
            self.edit_route
        )

        self.table.selectionModel().selectionChanged.connect(
            self.selection_changed
        )

        #
        # Initial state
        #

        self.update_button_states()

    #
    # Set train
    #

    def set_train(
        self,
        train,
    ):

        if train is None:

            self.train_id = None

            self.train_label.setText(
                "No train selected."
            )

            self.model.set_routes(
                []
            )

            self.update_button_states()

            return

        self.train_id = train.id

        number = (
            train.symbol
            or ""
        )

        name = (
            train.name
            or ""
        )

        self.train_label.setText(
            f"Train: {number} - {name}"
        )

        self.refresh()

    #
    # Set train ID
    #

    def set_train_id(
        self,
        train_id,
        train_name=None,
    ):

        self.train_id = train_id

        if train_id is None:

            self.train_label.setText(
                "No train selected."
            )

            self.model.set_routes(
                []
            )

        else:

            if train_name:

                self.train_label.setText(
                    f"Train: {train_name}"
                )

            else:

                self.train_label.setText(
                    f"Train ID: {train_id}"
                )

            self.refresh()

        self.update_button_states()

    #
    # Refresh
    #

    def refresh(
        self,
    ):

        if self.train_id is None:

            self.model.set_routes(
                []
            )

            self.update_button_states()

            return

        routes = (
            TrainRouteService.get_by_train(
                self.train_id
            )
        )

        self.model.set_routes(
            routes
        )

        self.table.resizeRowsToContents()

        if routes:

            first_index = self.model.index(
                0,
                0,
            )

            self.table.setCurrentIndex(
                first_index
            )

            self.table.selectRow(
                0
            )

            self.table.scrollTo(
                first_index,
                QAbstractItemView.PositionAtTop,
            )

        self.update_button_states()

    #
    # Get selected route
    #

    def get_selected_route(
        self,
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Train Route",
                "Please select a route stop.",
            )

            return None

        return self.model.get_route(
            indexes[0].row()
        )

    #
    # Get selected route without message
    #

    def get_selected_route_without_message(
        self,
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            return None

        return self.model.get_route(
            indexes[0].row()
        )

    #
    # Get selected route ID
    #

    def get_selected_route_id(
        self,
    ):

        route = (
            self.get_selected_route_without_message()
        )

        if route is None:

            return None

        return route.id

    #
    # Selection changed
    #

    def selection_changed(
        self,
        selected,
        deselected,
    ):

        self.update_button_states()

    #
    # Update button states
    #

    def update_button_states(
        self,
    ):

        route = (
            self.get_selected_route_without_message()
        )

        has_train = (
            self.train_id is not None
        )

        has_route = (
            route is not None
        )

        self.add_button.setEnabled(
            has_train
        )

        self.edit_button.setEnabled(
            has_route
        )

        self.delete_button.setEnabled(
            has_route
        )

        self.move_up_button.setEnabled(
            (
                has_route
                and route.sequence > 1
            )
            if has_route
            else False
        )

        self.move_down_button.setEnabled(
            (
                has_route
                and route.sequence
                < len(
                    self.model.routes
                )
            )
            if has_route
            else False
        )

        self.refresh_button.setEnabled(
            has_train
        )

    #
    # Add route
    #

    def add_route(
        self,
    ):

        if self.train_id is None:

            QMessageBox.information(
                self,
                "Train Route",
                "Please select a train first.",
            )

            return

        dialog = AddTrainRouteDialog(
            train_id=self.train_id,
            parent=self,
        )

        if (
            dialog.exec()
            == dialog.DialogCode.Accepted
        ):

            self.refresh()
            self.route_changed.emit()

    #
    # Edit route
    #

    def edit_route(
        self,
    ):

        route = (
            self.get_selected_route()
        )

        if route is None:

            return

        dialog = AddTrainRouteDialog(
            train_id=self.train_id,
            parent=self,
            route=route,
        )

        if (
            dialog.exec()
            == dialog.DialogCode.Accepted
        ):

            self.refresh()
            self.route_changed.emit()

    #
    # Move route up
    #

    def move_up(
        self,
    ):

        route = (
            self.get_selected_route()
        )

        if route is None:

            return

        success, result = (
            TrainRouteService.move_up(
                route.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Move Route Stop",
                str(
                    result
                ),
            )

            return

        self.refresh()
        self.route_changed.emit()

        for row, current_route in enumerate(
            self.model.routes
        ):

            if current_route.id == route.id:

                self.table.selectRow(
                    row
                )

                break

    #
    # Move route down
    #

    def move_down(
        self,
    ):

        route = (
            self.get_selected_route()
        )

        if route is None:

            return

        success, result = (
            TrainRouteService.move_down(
                route.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Move Route Stop",
                str(
                    result
                ),
            )

            return

        self.refresh()
        self.route_changed.emit()

        for row, current_route in enumerate(
            self.model.routes
        ):

            if current_route.id == route.id:

                self.table.selectRow(
                    row
                )

                break

    #
    # Delete route
    #

    def delete_route(
        self,
    ):

        route = (
            self.get_selected_route()
        )

        if route is None:

            return

        answer = QMessageBox.question(
            self,
            "Delete Route Stop",
            (
                f"Delete route stop "
                f"{route.sequence}: "
                f"'{route.location}'?\n\n"
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
            TrainRouteService.delete(
                route.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Delete Route Stop",
                str(
                    result
                ),
            )

            return

        self.refresh()
        self.route_changed.emit()
