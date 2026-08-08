from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
)

from modelrailroadops.ui.cars.roster_tab import RosterTab
from modelrailroadops.ui.industries.industry_tab import IndustryTab

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



class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()


        self.setWindowTitle(
            "Model Railroad Operations"
        )


        self.resize(
            1200,
            800
        )



        tabs = QTabWidget()



        tabs.addTab(
            RosterTab(),
            "Car Roster"
        )



        tabs.addTab(
            IndustryTab(),
            "Industries"
        )



        tabs.addTab(
            IndustryTracksWidget(),
            "Industry Tracks"
        )



        tabs.addTab(
            CarLocationsWidget(),
            "Car Locations"
        )



        tabs.addTab(
            SpotOccupancyWidget(),
            "Spot Occupancy"
        )



        tabs.addTab(
            SpotManagerWidget(),
            "Spots"
        )



        tabs.addTab(
            CarHistoryWidget(),
            "Car History"
        )



        self.setCentralWidget(
            tabs
        )