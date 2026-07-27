import sys
from modelrailroadops.database.database import initialize_database
from PySide6.QtWidgets import QApplication
from modelrailroadops.ui.main_window import MainWindow


class Application:
    """
    Main application controller.
    """

    def run(self) -> int:
        initialize_database()

        app = QApplication(sys.argv)

        window = MainWindow()
        window.show()

        return app.exec()


def main():
    application = Application()
    return application.run()


if __name__ == "__main__":
    raise SystemExit(main())
