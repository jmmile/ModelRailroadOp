"""Companion connection information and per-layout-directory startup preference."""

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QCheckBox, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from modelrailroadops.paths import DATA_DIRECTORY
from modelrailroadops.services.companion_controller import CompanionController


class CompanionPanel(QGroupBox):
    def __init__(self, parent=None, settings=None, controller=None):
        super().__init__("iPad / Web Companion", parent)
        self.settings = settings if settings is not None else QSettings(
            str(DATA_DIRECTORY / "desktop-settings.ini"), QSettings.IniFormat
        )
        self.controller = controller or CompanionController(self)
        layout = QVBoxLayout(self)
        self.details = QLabel()
        self.details.setWordWrap(True)
        self.details.setTextFormat(Qt.PlainText)
        self.details.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.details)
        row = QHBoxLayout()
        self.automatic = QCheckBox("Start companion automatically")
        self.automatic.setChecked(self.settings.value("companion/automatic", True, type=bool))
        self.automatic.toggled.connect(self.save_preference)
        row.addWidget(self.automatic)
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.start_button.clicked.connect(self.controller.start)
        self.stop_button.clicked.connect(self.controller.stop)
        row.addWidget(self.start_button)
        row.addWidget(self.stop_button)
        layout.addLayout(row)
        self.controller.changed.connect(self.refresh)
        self.refresh()

    def save_preference(self, enabled):
        self.settings.setValue("companion/automatic", enabled)
        self.settings.sync()

    def start_automatically(self):
        if self.automatic.isChecked():
            self.controller.start()

    def refresh(self):
        controller = self.controller
        text = controller.status
        if controller.status == "Running":
            text += f" — Pairing code: {controller.code}\n"
            text += controller.addresses or "No LAN address found. Check your network connection."
            text += "\nConnect the iPad to the same private network. Allow Windows Firewall private-network access only."
        self.details.setText(text)
        self.start_button.setEnabled(not controller.busy)
        self.stop_button.setEnabled(controller.busy and controller.status != "Stopping…")
