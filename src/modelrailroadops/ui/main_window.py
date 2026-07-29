from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
)

from modelrailroadops.ui.cars.roster_tab import RosterTab


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Model Railroad Operations")
        self.resize(1200, 800)

        tabs = QTabWidget()

        tabs.addTab(RosterTab(), "Car Roster")

        self.setCentralWidget(tabs)