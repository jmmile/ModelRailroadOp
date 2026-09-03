from PySide6.QtCore import (
    Qt,
    QSortFilterProxyModel,
)

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from modelrailroadops.services.locomotive_service import (
    LocomotiveService,
)

from modelrailroadops.ui.dialogs.add_locomotive_dialog import (
    AddLocomotiveDialog,
)

from modelrailroadops.ui.locomotives.locomotive_table_model import (
    LocomotiveTableModel,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)


class LocomotivesWidget(QWidget):
    """
    Displays and manages the locomotive roster.
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
        # Status
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
            QLabel(
                "Search"
            )
        )

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            (
                "Reporting Mark, Number, Owner, Model, "
                "Manufacturer, Type, Horsepower, Length, Status..."
            )
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
            "Add Locomotive"
        )

        self.edit_button = QPushButton(
            "Edit Locomotive"
        )

        self.delete_button = QPushButton(
            "Delete Locomotive"
        )

        self.import_button = QPushButton(
            "Import CSV"
        )

        self.export_button = QPushButton(
            "Export CSV"
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

        button_layout.addWidget(
            self.import_button
        )

        button_layout.addWidget(
            self.export_button
        )

        button_layout.addStretch()

        layout.addLayout(
            button_layout
        )

        #
        # Model
        #

        self.model = LocomotiveTableModel()

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

        self.proxy.setSortRole(
            Qt.DisplayRole
        )

        #
        # Table
        #

        self.table = QTableView()

        self.table.setModel(
            self.proxy
        )

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

        self.table.setSortingEnabled(
            True
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
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
            self.add_locomotive
        )

        self.edit_button.clicked.connect(
            self.edit_locomotive
        )

        self.delete_button.clicked.connect(
            self.delete_locomotive
        )

        self.import_button.clicked.connect(
            self.import_csv
        )

        self.export_button.clicked.connect(
            self.export_csv
        )

        self.table.doubleClicked.connect(
            self.edit_locomotive
        )

        #
        # Initial load
        #

        self.refresh()

        #
        # Start sorted by Reporting Mark.
        #

        self.proxy.sort(
            0,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            0,
            Qt.AscendingOrder
        )

    #
    # Refresh when the widget becomes visible.
    #

    def showEvent(
        self,
        event,
    ):

        super().showEvent(
            event
        )

        self.refresh()

        self.proxy.sort(
            0,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            0,
            Qt.AscendingOrder
        )

    #
    # Refresh
    #

    def refresh(self):

        self.model.refresh()

        self.proxy.invalidate()

        self.table.resizeColumnsToContents()

        total = self.model.rowCount()

        self.status_label.setText(
            f"{total} Locomotives"
        )

    #
    # Selected locomotive
    #

    def selected_locomotive(self):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            return None

        source_index = self.proxy.mapToSource(
            indexes[0]
        )

        return self.model.get_locomotive(
            source_index.row()
        )

    #
    # Add locomotive
    #

    def add_locomotive(self):

        dialog = AddLocomotiveDialog(
            self
        )

        if dialog.exec():

            self.refresh()

            self.proxy.sort(
                0,
                Qt.AscendingOrder
            )

    #
    # Edit locomotive
    #

    def edit_locomotive(
        self,
        index=None,
    ):

        locomotive = self.selected_locomotive()

        if locomotive is None:

            QMessageBox.information(
                self,
                "Edit Locomotive",
                "Please select a locomotive.",
            )

            return

        dialog = AddLocomotiveDialog(
            self,
            locomotive,
        )

        if dialog.exec():

            self.refresh()

            self.proxy.sort(
                0,
                Qt.AscendingOrder
            )

    #
    # Delete locomotive
    #

    def delete_locomotive(self):

        locomotive = self.selected_locomotive()

        if locomotive is None:

            QMessageBox.information(
                self,
                "Delete Locomotive",
                "Please select a locomotive.",
            )

            return

        result = QMessageBox.question(
            self,
            "Delete Locomotive",
            (
                f"Are you sure you want to delete "
                f"{locomotive.reporting_mark} "
                f"{locomotive.number}?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:

            return

        deleted = LocomotiveService.delete(
            locomotive.id
        )

        if not deleted:

            QMessageBox.warning(
                self,
                "Delete Locomotive",
                "The locomotive could not be deleted.",
            )

            return

        self.refresh()

        self.proxy.sort(
            0,
            Qt.AscendingOrder
        )

    #
    # Export CSV
    #

    def export_csv(self):

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Locomotive Roster",
            "",
            "CSV Files (*.csv)",
        )

        if not filepath:

            return

        try:

            self.model.export_to_csv(
                filepath
            )

            QMessageBox.information(
                self,
                "Export Complete",
                (
                    "The locomotive roster was "
                    "exported successfully."
                ),
            )

        except Exception as ex:

            QMessageBox.warning(
                self,
                "Export Failed",
                str(ex),
            )

    #
    # Import CSV
    #

    def import_csv(self):

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Locomotive Roster",
            "",
            "CSV Files (*.csv)",
        )

        if not filepath:

            return

        try:

            added, skipped = (
                self.model.import_from_csv(
                    filepath
                )
            )

        except Exception as ex:

            QMessageBox.critical(
                self,
                "Import Failed",
                str(ex),
            )

            return

        self.refresh()

        self.proxy.sort(
            0,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            0,
            Qt.AscendingOrder
        )

        total = self.model.rowCount()

        QMessageBox.information(
            self,
            "Import Complete",
            (
                f"Imported: {added}\n"
                f"Skipped: {skipped}\n\n"
                f"Roster now contains "
                f"{total} locomotives."
            ),
        )