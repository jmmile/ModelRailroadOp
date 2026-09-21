import logging
import sys
from logging.handlers import RotatingFileHandler

from PySide6.QtWidgets import QApplication, QMessageBox

from modelrailroadops.database.database import (
    DATABASE_FILE,
    initialize_database,
)
from modelrailroadops.paths import (
    DATA_DIRECTORY,
    data_directory_override,
)
from modelrailroadops.ui.main_window import MainWindow


class Application:
    """
    Main application controller.
    """

    def run(self) -> int:
        app = QApplication(sys.argv)

        try:
            log_directory = DATA_DIRECTORY / "logs"
            log_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            logging.basicConfig(
                handlers=[
                    RotatingFileHandler(
                        log_directory / "application.log",
                        maxBytes=1000000,
                        backupCount=3,
                        encoding="utf-8",
                    )
                ],
                level=logging.INFO,
                format="%(asctime)s %(levelname)s %(message)s",
            )

            initialize_database()

            window = MainWindow()
            window.show()
            window.dashboard_widget.companion_panel.start_automatically()

            if data_directory_override() is not None:
                QMessageBox.warning(
                    window,
                    "Database Override Active",
                    (
                        "DATABASE OVERRIDE ACTIVE\n\n"
                        "Model Railroad Operations is not using "
                        "its normal data directory.\n\n"
                        "Database:\n"
                        f"{DATABASE_FILE}\n\n"
                        "This is normally used for testing. "
                        "Changes made during this run will be "
                        "saved to the database shown above."
                    ),
                )

            return app.exec()

        except Exception:  # noqa: BLE001 - show startup failures without a console
            logging.exception(
                "Application startup failed"
            )

            QMessageBox.critical(
                None,
                "Unable to Start",
                (
                    "The application could not start. "
                    "Details are in "
                    f"{DATA_DIRECTORY / 'logs' / 'application.log'}."
                ),
            )

            return 1


def main():
    application = Application()

    return application.run()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
