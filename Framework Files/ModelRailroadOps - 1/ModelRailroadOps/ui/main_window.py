from PySide6.QtWidgets import QMainWindow,QTabWidget
from config import APP_NAME
from ui.dashboard import Dashboard
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1000,700)
        tabs=QTabWidget()
        tabs.addTab(Dashboard(),'Dashboard')
        self.setCentralWidget(tabs)
