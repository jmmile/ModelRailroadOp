import sys

from PySide6.QtWidgets import QApplication

from modelrailroadops.ui.main_window import MainWindow


class Application:
    """
    Main application controller.
    """

    def run(self) -> int:
        app = QApplication(sys.argv)

        window = MainWindow()
        window.show()

        return app.exec()