from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QStatusBar,
)

from config import APP_NAME
from ui.dashboard import Dashboard
from ui.cars.roster_tab import RosterTab


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)

        self.tabs = QTabWidget()

        # Create the tabs
        self.dashboard = Dashboard()
        self.roster = RosterTab()

        # Add the tabs
        self.tabs.addTab(self.dashboard, "Dashboard")
        self.tabs.addTab(self.roster, "Cars")

        self.setCentralWidget(self.tabs)

        self.build_menu()

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

    def build_menu(self):

        menu = self.menuBar()

        menu.addMenu("File")
        menu.addMenu("Railroad")
        menu.addMenu("Reports")
        menu.addMenu("Tools")
        menu.addMenu("Help")