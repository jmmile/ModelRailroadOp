import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication

from modelrailroadops.ui.dialogs.add_car_dialog import AddCarDialog

app = QApplication(sys.argv)

dialog = AddCarDialog()
dialog.show()

sys.exit(app.exec())