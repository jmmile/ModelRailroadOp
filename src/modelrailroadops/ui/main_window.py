from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
)

from modelrailroadops.ui.cars.roster_tab import (
    RosterTab,
)

from modelrailroadops.ui.industries.industry_tab import (
    IndustryTab,
)

from modelrailroadops.ui.widgets.industry_tracks_widget import (
    IndustryTracksWidget,
)

from modelrailroadops.ui.widgets.car_locations_widget import (
    CarLocationsWidget,
)

from modelrailroadops.ui.widgets.spot_occupancy_widget import (
    SpotOccupancyWidget,
)

from modelrailroadops.ui.widgets.spot_manager_widget import (
    SpotManagerWidget,
)

from modelrailroadops.ui.widgets.car_history_widget import (
    CarHistoryWidget,
)

from modelrailroadops.ui.waybills.waybills_widget import (
    WaybillsWidget,
)

from modelrailroadops.ui.operations.operations_sessions_widget import (
    OperationsSessionsWidget,
)

from modelrailroadops.ui.switch_list.switch_list_widget import (
    SwitchListWidget,
)

from modelrailroadops.ui.trains.trains_widget import (
    TrainsWidget,
)

from modelrailroadops.ui.widgets.locations_widget import (
    LocationsWidget,
)

from modelrailroadops.ui.locomotives.locomotives_widget import (
    LocomotivesWidget,
)

from modelrailroadops.ui.passenger_cars.passenger_cars_widget import (
    PassengerCarsWidget,
)


class MainWindow(QMainWindow):
    """
    Main application window.

    Database-backed tabs are refreshed whenever the user
    selects the corresponding tab.

    The Industries tab also emits an industry_changed
    signal whenever an industry is added, edited, or deleted.
    MainWindow receives that signal and immediately refreshes
    the Industry Tracks widget.
    """

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Model Railroad Operations"
        )

        self.resize(
            1200,
            800,
        )

        #
        # Main tab widget
        #

        self.tabs = QTabWidget()

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
        # Industries
        #

        self.industry_tab = IndustryTab()

        self.tabs.addTab(
            self.industry_tab,
            "Industries",
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

        #
        # When the Industries tab changes the database,
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

    #
    # Industry database changed
    #

    def industry_changed(
        self,
    ):
        """
        Called whenever the Industries tab adds,
        edits, or deletes an industry.

        Refresh Industry Tracks immediately from
        the database.
        """

        self.industry_tracks_widget.refresh()

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

        if widget is self.roster_tab:

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
        # Industries
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