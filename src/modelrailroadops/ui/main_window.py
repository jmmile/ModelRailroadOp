from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
)

from modelrailroadops.services.database_backup_service import (
    DatabaseBackupService,
)
from modelrailroadops.ui.cars.roster_tab import (
    RosterTab,
)
from modelrailroadops.ui.industries.industry_tab import (
    IndustryTab,
)
from modelrailroadops.ui.locomotives.locomotives_widget import (
    LocomotivesWidget,
)
from modelrailroadops.ui.operations.operations_sessions_widget import (
    OperationsSessionsWidget,
)
from modelrailroadops.ui.passenger_cars.passenger_cars_widget import (
    PassengerCarsWidget,
)
from modelrailroadops.ui.switch_list.switch_list_widget import (
    SwitchListWidget,
)
from modelrailroadops.ui.trains.trains_widget import (
    TrainsWidget,
)
from modelrailroadops.ui.waybills.waybills_widget import (
    WaybillsWidget,
)
from modelrailroadops.ui.widgets.car_history_widget import (
    CarHistoryWidget,
)
from modelrailroadops.ui.widgets.car_locations_widget import (
    CarLocationsWidget,
)
from modelrailroadops.ui.widgets.dashboard_widget import DashboardWidget
from modelrailroadops.ui.widgets.industry_tracks_widget import (
    IndustryTracksWidget,
)
from modelrailroadops.ui.widgets.locations_widget import (
    LocationsWidget,
)
from modelrailroadops.ui.widgets.spot_manager_widget import (
    SpotManagerWidget,
)
from modelrailroadops.ui.widgets.spot_occupancy_widget import (
    SpotOccupancyWidget,
)
from modelrailroadops.ui.widgets.track_diagram_widget import (
    TrackDiagramWidget,
)


class MainWindow(QMainWindow):
    """
    Main application window.

    Database-backed tabs are refreshed whenever the user
    selects the corresponding tab.

    The Freight Industries tab also emits an industry_changed
    signal whenever an industry is added, edited, or deleted.
    MainWindow receives that signal and immediately refreshes
    the Industry Tracks widget.
    """

    def __init__(self):

        super().__init__()
        self.setWindowIcon(QIcon(str(
            Path(__file__).resolve().parents[1] / "resources" / "application.ico"
        )))

        self.setWindowTitle(
            "Model Railroad Operations"
        )

        self.resize(
            1200,
            800,
        )

        self.create_file_menu()

        #
        # Main tab widget
        #

        self.tabs = QTabWidget()

        #
        # Dashboard
        #

        self.dashboard_widget = DashboardWidget()
        self.dashboard_widget.backup_requested.connect(self.backup_database)
        self.dashboard_widget.restore_requested.connect(self.restore_database)
        self.dashboard_widget.navigate_requested.connect(self.open_tab)
        self.tabs.addTab(self.dashboard_widget, "Dashboard")

        self.dashboard_button = QPushButton("Dashboard")
        self.dashboard_button.setToolTip("Return to the Dashboard")
        self.dashboard_button.clicked.connect(self.open_dashboard)
        self.tabs.setCornerWidget(
            self.dashboard_button,
            Qt.TopRightCorner,
        )

        #
        # Car Roster
        #

        self.roster_tab = RosterTab()

        self.tabs.addTab(
            self.roster_tab,
            "Car Roster",
        )

        #
        # Motive Power
        #

        self.locomotives_widget = (
            LocomotivesWidget()
        )

        self.tabs.addTab(
            self.locomotives_widget,
            "Motive Power",
        )

        #
        # Passenger Equipment
        #

        self.passenger_cars_widget = (
            PassengerCarsWidget()
        )

        self.tabs.addTab(
            self.passenger_cars_widget,
            "Passenger Equipment",
        )

        #
        # Freight Industries
        #

        self.industry_tab = IndustryTab()

        self.tabs.addTab(
            self.industry_tab,
            "Freight Industries",
        )

        #
        # Industry Tracks
        #

        self.industry_tracks_widget = (
            IndustryTracksWidget()
        )

        self.tabs.addTab(
            self.industry_tracks_widget,
            "Industry Tracks",
        )

        #
        # General railroad locations and tracks
        #

        self.locations_widget = LocationsWidget()

        self.tabs.addTab(
            self.locations_widget,
            "Locations",
        )

        self.track_diagram_widget = TrackDiagramWidget()

        self.tabs.addTab(
            self.track_diagram_widget,
            "Car Spotting",
        )

        #
        # When the Freight Industries tab changes the database,
        # immediately refresh Industry Tracks.
        #

        self.industry_tab.industry_changed.connect(
            self.industry_changed
        )

        #
        # Car Locations
        #

        self.car_locations_widget = (
            CarLocationsWidget()
        )

        self.tabs.addTab(
            self.car_locations_widget,
            "Car Locations",
        )

        #
        # Spot Occupancy
        #

        self.spot_occupancy_widget = (
            SpotOccupancyWidget()
        )

        self.tabs.addTab(
            self.spot_occupancy_widget,
            "Spot Occupancy",
        )

        #
        # Spot Manager
        #

        self.spot_manager_widget = (
            SpotManagerWidget()
        )

        self.tabs.addTab(
            self.spot_manager_widget,
            "Spots",
        )

        #
        # Car History
        #

        self.car_history_widget = (
            CarHistoryWidget()
        )

        self.tabs.addTab(
            self.car_history_widget,
            "Car History",
        )

        #
        # Waybills
        #

        self.waybills_widget = (
            WaybillsWidget()
        )

        self.tabs.addTab(
            self.waybills_widget,
            "Waybills",
        )

        #
        # Operations Sessions
        #

        self.operations_sessions_widget = (
            OperationsSessionsWidget()
        )

        self.tabs.addTab(
            self.operations_sessions_widget,
            "Operations Sessions",
        )

        #
        # Switch List
        #

        self.switch_list_widget = (
            SwitchListWidget()
        )

        self.tabs.addTab(
            self.switch_list_widget,
            "Switch List",
        )

        #
        # Trains
        #

        self.trains_widget = (
            TrainsWidget()
        )

        self.tabs.addTab(
            self.trains_widget,
            "Trains",
        )

        #
        # Refresh the appropriate tab whenever
        # the user selects a different tab.
        #

        self.tabs.currentChanged.connect(
            self.tab_changed
        )

        #
        # Set central widget
        #

        self.setCentralWidget(
            self.tabs
        )

    def closeEvent(self, event):
        controller = self.dashboard_widget.companion_panel.controller
        if controller.busy:
            controller.stop()
            event.ignore()
            QTimer.singleShot(200, self.close)
            return
        super().closeEvent(event)

    def create_file_menu(self):
        self.file_menu = self.menuBar().addMenu("File")

        self.backup_database_action = self.file_menu.addAction(
            "Backup Database..."
        )
        self.backup_database_action.triggered.connect(self.backup_database)

        self.restore_database_action = self.file_menu.addAction(
            "Restore Database..."
        )
        self.restore_database_action.triggered.connect(self.restore_database)

    def backup_database(self):
        default_path = DatabaseBackupService.default_backup_path()
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Backup Database",
            str(default_path),
            "Complete Layout Backup (*.zip)",
        )

        if not filepath:
            return
        if not filepath.lower().endswith(".zip"):
            filepath += ".zip"

        created, result = DatabaseBackupService.create_backup(filepath)
        if not created:
            QMessageBox.warning(self, "Backup Failed", result)
            return

        QMessageBox.information(
            self,
            "Backup Complete",
            f"The database and managed pictures (cars, locomotives, and passenger equipment) were backed up to:\n\n{result}",
        )

    def restore_database(self):
        if self.dashboard_widget.companion_panel.controller.busy:
            QMessageBox.warning(
                self, "Stop Companion First",
                "Stop the companion on the Dashboard before restoring a backup. "
                "Also close any separately running companion server.",
            )
            return
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Restore Database",
            str(DatabaseBackupService.default_backup_path().parent),
            "Layout and Database Backups (*.zip *.db)",
        )

        if not filepath:
            return

        answer = QMessageBox.question(
            self,
            "Restore Database",
            (
                "Restore this backup? ZIP backups replace the database and included picture collections. "
                "Older backups without locomotive or passenger pictures leave those collections unchanged. "
                "Older DB backups replace only the database.\n\n"
                f"{filepath}\n\n"
                "A safety backup will be created first (including all managed pictures for ZIP restores)."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        restored, result = DatabaseBackupService.restore_backup(filepath)
        if not restored:
            QMessageBox.critical(self, "Restore Failed", result)
            return

        for index in range(self.tabs.count()):
            self.tab_changed(index)

        QMessageBox.information(
            self,
            "Restore Complete",
            (
                "The database was restored successfully.\n\n"
                "The database that was active before the restore was saved to:\n\n"
                f"{result}"
            ),
        )

    #
    # Industry database changed
    #

    def industry_changed(
        self,
    ):
        """
        Called whenever the Freight Industries tab adds,
        edits, or deletes an industry.

        Refresh Industry Tracks immediately from
        the database.
        """

        self.industry_tracks_widget.refresh()

    def open_tab(self, tab_name):
        for index in range(self.tabs.count()):
            if self.tabs.tabText(index) == tab_name:
                self.tabs.setCurrentIndex(index)
                return

    def open_dashboard(self):
        self.tabs.setCurrentWidget(self.dashboard_widget)

    #
    # Tab changed
    #

    def tab_changed(
        self,
        index,
    ):
        """
        Refresh the database-backed widget when
        the user selects a different tab.
        """

        widget = self.tabs.widget(
            index
        )

        #
        # Car Roster
        #

        if widget is self.dashboard_widget:

            self.dashboard_widget.refresh()

        elif widget is self.roster_tab:

            self.roster_tab.refresh()

        #
        # Motive Power
        #

        elif widget is self.locomotives_widget:

            self.locomotives_widget.refresh()

        #
        # Passenger Equipment
        #

        elif widget is self.passenger_cars_widget:

            self.passenger_cars_widget.refresh()

        #
        # Freight Industries
        #

        elif widget is self.industry_tab:

            self.industry_tab.refresh()

        #
        # Industry Tracks
        #

        elif widget is self.industry_tracks_widget:

            self.industry_tracks_widget.refresh()

        #
        # Locations
        #

        elif widget is self.locations_widget:

            self.locations_widget.refresh()

        elif widget is self.track_diagram_widget:

            self.track_diagram_widget.refresh(force=True)

        #
        # Car Locations
        #

        elif widget is self.car_locations_widget:

            self.car_locations_widget.refresh()

        #
        # Spot Occupancy
        #

        elif widget is self.spot_occupancy_widget:

            self.spot_occupancy_widget.apply_filters()

        #
        # Spot Manager
        #

        elif widget is self.spot_manager_widget:

            if hasattr(
                self.spot_manager_widget,
                "refresh",
            ):

                self.spot_manager_widget.refresh()

        #
        # Car History
        #

        elif widget is self.car_history_widget:

            if hasattr(
                self.car_history_widget,
                "refresh",
            ):

                self.car_history_widget.refresh()

        #
        # Waybills
        #

        elif widget is self.waybills_widget:

            if hasattr(
                self.waybills_widget,
                "refresh",
            ):

                self.waybills_widget.refresh()

        #
        # Operations Sessions
        #

        elif widget is self.operations_sessions_widget:

            if hasattr(
                self.operations_sessions_widget,
                "refresh",
            ):

                self.operations_sessions_widget.refresh()

        #
        # Switch List
        #

        elif widget is self.switch_list_widget:

            if hasattr(
                self.switch_list_widget,
                "refresh",
            ):

                self.switch_list_widget.refresh()

        #
        # Trains
        #

        elif widget is self.trains_widget:

            if hasattr(
                self.trains_widget,
                "refresh",
            ):

                self.trains_widget.refresh()
