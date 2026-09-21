from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
)

from modelrailroadops.services.dashboard_service import DashboardService
from modelrailroadops.ui.widgets.companion_panel import CompanionPanel


class DashboardWidget(QWidget):
    """Opening overview of the railroad's current operating state."""

    navigate_requested = Signal(str)
    backup_requested = Signal()
    restore_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        heading = QLabel("Railroad Operations Dashboard")
        heading.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(heading)

        self.updated_label = QLabel()
        self.updated_label.setStyleSheet("color: #555;")
        layout.addWidget(self.updated_label)
        self.companion_panel = CompanionPanel(self)
        layout.addWidget(self.companion_panel)

        grid = QGridLayout()
        layout.addLayout(grid)

        operations_box = QGroupBox("Current Operations")
        operations_layout = QVBoxLayout(operations_box)
        self.session_label = QLabel()
        self.session_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.session_detail_label = QLabel()
        self.session_progress = QProgressBar()
        self.session_progress.setRange(0, 100)
        operations_layout.addWidget(self.session_label)
        operations_layout.addWidget(self.session_detail_label)
        operations_layout.addWidget(self.session_progress)
        operations_layout.addWidget(
            self._navigation_button("Open Operations Session", "Operations Sessions")
        )
        grid.addWidget(operations_box, 0, 0)

        fleet_box = QGroupBox("Fleet Summary")
        fleet_layout = QVBoxLayout(fleet_box)
        self.fleet_label = QLabel()
        fleet_layout.addWidget(self.fleet_label)
        fleet_layout.addStretch()
        fleet_layout.addWidget(self._navigation_button("Open Car Roster", "Car Roster"))
        grid.addWidget(fleet_box, 0, 1)

        work_box = QGroupBox("Work Waiting")
        work_layout = QVBoxLayout(work_box)
        self.work_label = QLabel()
        work_layout.addWidget(self.work_label)
        work_layout.addStretch()
        work_buttons = QHBoxLayout()
        work_buttons.addWidget(
            self._navigation_button("Industry Demand", "Freight Industries")
        )
        work_buttons.addWidget(
            self._navigation_button("Open Switch List", "Switch List")
        )
        work_layout.addLayout(work_buttons)
        grid.addWidget(work_box, 1, 0)

        attention_box = QGroupBox("Attention Needed")
        attention_layout = QVBoxLayout(attention_box)
        self.attention_label = QLabel()
        self.attention_label.setWordWrap(True)
        attention_layout.addWidget(self.attention_label)
        attention_layout.addStretch()
        attention_layout.addWidget(
            self._navigation_button("Open Car Spotting", "Car Spotting")
        )
        grid.addWidget(attention_box, 1, 1)

        capacity_box = QGroupBox("Track Capacity — Near capacity means 80% or more")
        capacity_layout = QVBoxLayout(capacity_box)
        self.capacity_table = QTableWidget(0, 6)
        self.capacity_table.setHorizontalHeaderLabels(
            ["Location", "Track", "Cars", "Capacity", "Available", "Status"]
        )
        self.capacity_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.capacity_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.capacity_table.horizontalHeader().setStretchLastSection(True)
        capacity_layout.addWidget(self.capacity_table)
        capacity_layout.addWidget(
            self._navigation_button("Open Locations", "Locations")
        )
        layout.addWidget(capacity_box)

        backups = QHBoxLayout()
        self.backup_button = QPushButton("Backup Database…")
        self.backup_button.clicked.connect(self.backup_requested.emit)
        self.restore_button = QPushButton("Restore Database…")
        self.restore_button.clicked.connect(self.restore_requested.emit)
        backups.addWidget(self.backup_button)
        backups.addWidget(self.restore_button)
        backups.addWidget(
            QLabel(
                "Manual ZIP backups include the database and all managed pictures.\nAutomatic session backups: database only; latest 10 retained."
            )
        )
        layout.addLayout(backups)

        controls = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Dashboard")
        self.refresh_button.clicked.connect(self.refresh)
        controls.addWidget(self.refresh_button)
        controls.addStretch()
        layout.addLayout(controls)
        layout.addStretch()

        self.refresh()

    def _navigation_button(self, text, destination):
        button = QPushButton(text)
        button.clicked.connect(
            lambda _checked=False, tab=destination: self.navigate_requested.emit(tab)
        )
        return button

    def refresh(self):
        summary = DashboardService.get_summary()
        rows = summary["capacity_details"]
        self.capacity_table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            for column, key in enumerate(
                ("location", "track", "occupied", "capacity", "available", "status")
            ):
                value = row[key]
                self.capacity_table.setItem(
                    index,
                    column,
                    QTableWidgetItem(str(value) if value is not None else "Not set"),
                )
        operations = summary["current_operations"]
        fleet = summary["fleet"]
        work = summary["work_waiting"]

        self.session_label.setText(operations["name"])
        details = []
        if operations["date"]:
            details.append(f"Date: {operations['date']}")
        details.append(f"Train(s): {operations['trains']}")
        details.append(
            "Moves completed: "
            f"{operations['completed_moves']} of {operations['total_moves']}"
        )
        self.session_detail_label.setText("\n".join(details))
        self.session_progress.setValue(operations["progress"])
        self.session_progress.setFormat(f"{operations['progress']}% complete")

        self.fleet_label.setText(
            f"Total freight cars: {fleet['total']}\n"
            f"Loaded: {fleet['loaded']}\n"
            f"Empty: {fleet['empty']}\n"
            f"Available: {fleet['available']}\n"
            f"On trains: {fleet['on_train']}\n"
            f"Unassigned: {fleet['unassigned']}"
        )

        self.work_label.setText(
            f"Industry demands: {work['industry_demands']}\n"
            f"Active waybills: {work['active_waybills']}\n"
            f"Pending switch-list moves: {work['pending_moves']}\n"
            f"Cars awaiting pickup: {work['awaiting_pickup']}"
        )

        active_attention = [
            f"{item['label']}: {item['count']}"
            for item in summary["attention"]
            if item["count"]
        ]
        if active_attention:
            self.attention_label.setText("\n".join(active_attention))
            self.attention_label.setStyleSheet("color: #a00000; font-weight: bold;")
        else:
            self.attention_label.setText("No problems detected.")
            self.attention_label.setStyleSheet("color: #207020; font-weight: bold;")

        self.updated_label.setText("Dashboard refreshed from current railroad data.")
