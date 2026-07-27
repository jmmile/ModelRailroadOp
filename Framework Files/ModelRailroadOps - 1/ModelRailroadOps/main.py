import sys
from PySide6.QtWidgets import QApplication
from database import initialize_database
from ui.main_window import MainWindow

initialize_database()
app=QApplication(sys.argv)
w=MainWindow()
w.show()
sys.exit(app.exec())
