import sys

from PySide6.QtWidgets import QApplication

from modelrailroadops.database.database import initialize_database

from modelrailroadops.ui.main_window import MainWindow

from modelrailroadops.ui.styles import APPLICATION_STYLE



class Application:
    """
    Main application controller.
    """

    def run(self) -> int:

        initialize_database()


        app = QApplication(
            sys.argv
        )


        #
        # Global application style
        #
        app.setStyleSheet(
            APPLICATION_STYLE
        )


        window = MainWindow()

        window.show()


        return app.exec()



def main():

    application = Application()

    return application.run()



if __name__ == "__main__":

    raise SystemExit(
        main()
    )