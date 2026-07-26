"""
Model Railroad Operations Manager

Application entry point.
"""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from modelrailroadops.config import APP_NAME
from modelrailroadops.database import initialize_database
from modelrailroadops.logging_config import configure_logging
from modelrailroadops.ui.main_window import MainWindow


def main() -> int:
    """
    Application entry point.
    """

    configure_logging()

    logging.info("Starting %s", APP_NAME)

    try:
        initialize_database()

        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)

        window = MainWindow()
        window.show()

        return app.exec()

    except Exception:
        logging.exception("Fatal application error")

        try:
            app = QApplication.instance() or QApplication(sys.argv)

            QMessageBox.critical(
                None,
                APP_NAME,
                "A fatal error occurred while starting the application.\n\n"
                "See logs/application.log for details."
            )
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    sys.exit(main())