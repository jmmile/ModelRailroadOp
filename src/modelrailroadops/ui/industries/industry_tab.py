from PySide6.QtCore import (
    Qt,
    QSortFilterProxyModel,
    Signal,
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableView,
    QLineEdit,
    QLabel,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
)

from modelrailroadops.ui.industries.industry_table_model import (
    IndustryTableModel,
)

from modelrailroadops.ui.dialogs.add_industry_dialog import (
    AddIndustryDialog,
)

from modelrailroadops.services.industry_service import (
    IndustryService,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)


class IndustryTab(QWidget):
    """
    Displays and manages industries.

    Emits industry_changed whenever an industry has been
    successfully added, edited, or deleted.
    """

    #
    # Emitted after the database has been changed.
    #
    industry_changed = Signal()

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        #
        # Status Label
        #

        self.status_label = QLabel()

        layout.addWidget(
            self.status_label
        )

        #
        # Search
        #

        search_layout = QHBoxLayout()

        search_layout.addWidget(
            QLabel("Search")
        )

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            "Search industries..."
        )

        search_layout.addWidget(
            self.search_box
        )

        layout.addLayout(
            search_layout
        )

        #
        # Buttons
        #

        button_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "Add Industry"
        )

        self.edit_button = QPushButton(
            "Edit Industry"
        )

        self.delete_button = QPushButton(
            "Delete Industry"
        )

        button_layout.addWidget(
            self.add_button
        )

        button_layout.addWidget(
            self.edit_button
        )

        button_layout.addWidget(
            self.delete_button
        )

        button_layout.addStretch()

        layout.addLayout(
            button_layout
        )

        #
        # Model
        #

        self.model = IndustryTableModel()

        self.proxy = QSortFilterProxyModel(
            self
        )

        self.proxy.setSourceModel(
            self.model
        )

        self.proxy.setFilterCaseSensitivity(
            Qt.CaseInsensitive
        )

        self.proxy.setFilterKeyColumn(
            -1
        )

        #
        # Table
        #

        self.table = QTableView()

        self.table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.table.setModel(
            self.proxy
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

        self.table.setSortingEnabled(
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
        # Signals
        #

        self.search_box.textChanged.connect(
            self.proxy.setFilterRegularExpression
        )

        self.add_button.clicked.connect(
            self.add_industry
        )

        self.edit_button.clicked.connect(
            self.edit_industry
        )

        self.delete_button.clicked.connect(
            self.delete_industry
        )

        self.table.doubleClicked.connect(
            self.edit_industry
        )

        #
        # IMPORTANT:
        #
        # The table uses a QSortFilterProxyModel, so the
        # selection must be monitored on the table's
        # selection model.
        #

        self.table.selectionModel().selectionChanged.connect(
            self.industry_selection_changed
        )

        #
        # Initial button state
        #

        self.update_button_state()

        #
        # Initial database load
        #

        self.refresh()

    #
    # Update button state
    #

    def update_button_state(
        self
    ):

        has_selection = bool(
            self.table.selectionModel()
            .selectedRows()
        )

        #
        # Add Industry is always available.
        #

        self.add_button.setEnabled(
            True
        )

        #
        # Edit and Delete require a selected
        # industry.
        #

        self.edit_button.setEnabled(
            has_selection
        )

        self.delete_button.setEnabled(
            has_selection
        )

    #
    # Industry selection changed
    #

    def industry_selection_changed(
        self,
        selected,
        deselected,
    ):

        self.update_button_state()

    #
    # Refresh
    #

    def refresh(self):
        """
        Reload industries directly from the database.
        """

        self.model.refresh()

        self.table.resizeColumnsToContents()

        self.status_label.setText(
            f"{self.model.rowCount()} industries"
        )

        #
        # Refreshing the model can change or remove the
        # current selection, so update the buttons after
        # the model has been refreshed.
        #

        self.update_button_state()

    #
    # Show Event
    #

    def showEvent(
        self,
        event
    ):
        """
        Refresh data whenever this tab becomes visible.
        """

        self.refresh()

        super().showEvent(
            event
        )

    #
    # Add Industry
    #

    def add_industry(
        self
    ):

        dialog = AddIndustryDialog(
            self
        )

        if dialog.exec():

            #
            # The dialog has already committed the
            # industry to the database.
            #

            self.refresh()

            #
            # Tell MainWindow that the industry database
            # has changed.
            #

            self.industry_changed.emit()

    #
    # Edit Industry
    #

    def edit_industry(
        self,
        index=None
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        #
        # When called by double-click, use the supplied
        # index if there is not currently a selection.
        #

        if not indexes and index is not None:

            if index.isValid():

                indexes = [
                    index
                ]

        if not indexes:

            QMessageBox.information(
                self,
                "Edit Industry",
                "Please select an industry."
            )

            return

        proxy_index = indexes[0]

        source_index = (
            self.proxy.mapToSource(
                proxy_index
            )
        )

        industry = (
            self.model.get_industry(
                source_index.row()
            )
        )

        if industry is None:

            QMessageBox.warning(
                self,
                "Edit Industry",
                "The selected industry could not be found."
            )

            return

        dialog = AddIndustryDialog(
            self,
            industry
        )

        if dialog.exec():

            self.refresh()

            #
            # Tell MainWindow that the industry database
            # has changed.
            #

            self.industry_changed.emit()

    #
    # Delete Industry
    #

    def delete_industry(
        self
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Delete Industry",
                "Please select an industry."
            )

            return

        proxy_index = indexes[0]

        source_index = (
            self.proxy.mapToSource(
                proxy_index
            )
        )

        industry = (
            self.model.get_industry(
                source_index.row()
            )
        )

        if industry is None:

            QMessageBox.warning(
                self,
                "Delete Industry",
                "The selected industry could not be found."
            )

            return

        answer = QMessageBox.question(
            self,
            "Delete Industry",
            f"Delete '{industry.name}'?",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer == QMessageBox.Yes:

            result = IndustryService.delete(
                industry.id
            )

            if result:

                self.refresh()

                #
                # Tell MainWindow that the industry
                # database has changed.
                #

                self.industry_changed.emit()

            else:

                QMessageBox.warning(
                    self,
                    "Delete Industry",
                    "The industry could not be deleted."
                )

                self.update_button_state()