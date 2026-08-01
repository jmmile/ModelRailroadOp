from PySide6.QtCore import Qt, QSortFilterProxyModel
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

from modelrailroadops.ui.industries.industry_table_model import IndustryTableModel
from modelrailroadops.ui.dialogs.add_industry_dialog import AddIndustryDialog
from modelrailroadops.services.industry_service import IndustryService


class IndustryTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        #
        # Status Label
        #
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        #
        # Search
        #
        search_layout = QHBoxLayout()

        search_layout.addWidget(QLabel("Search"))

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "Search industries..."
        )

        search_layout.addWidget(self.search_box)

        layout.addLayout(search_layout)

        #
        # Buttons
        #
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Industry")
        self.edit_button = QPushButton("Edit Industry")
        self.delete_button = QPushButton("Delete Industry")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        #
        # Model
        #
        self.model = IndustryTableModel()

        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)

        #
        # Table
        #
        self.table = QTableView()

        self.table.setModel(self.proxy)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.setAlternatingRowColors(True)

        self.table.setSortingEnabled(True)

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table)

        #
        # Signals
        #
        self.search_box.textChanged.connect(
            self.proxy.setFilterRegularExpression
        )

        self.add_button.clicked.connect(self.add_industry)
        self.edit_button.clicked.connect(self.edit_industry)
        self.delete_button.clicked.connect(self.delete_industry)

        self.table.doubleClicked.connect(self.edit_industry)

        self.refresh()

    def refresh(self):

        self.model.refresh()

        self.table.resizeColumnsToContents()

        self.status_label.setText(
            f"{self.model.rowCount()} industries"
        )

    def add_industry(self):

        dialog = AddIndustryDialog(self)

        if dialog.exec():
            self.refresh()

    def edit_industry(self, index=None):

        indexes = self.table.selectionModel().selectedRows()

        if not indexes:
            QMessageBox.information(
                self,
                "Edit Industry",
                "Please select an industry."
            )
            return

        proxy_index = indexes[0]
        source_index = self.proxy.mapToSource(proxy_index)

        industry = self.model.get_industry(source_index.row())

        dialog = AddIndustryDialog(self, industry)

        if dialog.exec():
            self.refresh()

    def delete_industry(self):

        indexes = self.table.selectionModel().selectedRows()

        if not indexes:
            QMessageBox.information(
                self,
                "Delete Industry",
                "Please select an industry."
            )
            return

        proxy_index = indexes[0]
        source_index = self.proxy.mapToSource(proxy_index)

        industry = self.model.get_industry(source_index.row())

        answer = QMessageBox.question(
            self,
            "Delete Industry",
            f"Delete '{industry.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer == QMessageBox.Yes:
            IndustryService.delete(industry.id)
            self.refresh()