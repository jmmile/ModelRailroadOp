from PySide6.QtCore import (
    QAbstractTableModel,
    Qt,
)

from PySide6.QtGui import (
    QColor,
    QBrush,
)

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.spot import Spot
from modelrailroadops.models.industry_track import IndustryTrack


class SpotOccupancyTableModel(QAbstractTableModel):

    HEADERS = [
        "Industry",
        "Track",
        "Spot",
        "Car",
        "Car Type",
    ]


    def __init__(self):

        super().__init__()

        self.rows = []

        self.load_data()


    def rowCount(
        self,
        parent=None
    ):

        return len(self.rows)


    def columnCount(
        self,
        parent=None
    ):

        return len(self.HEADERS)


    def headerData(
        self,
        section,
        orientation,
        role=Qt.DisplayRole
    ):

        if (
            role == Qt.DisplayRole
            and orientation == Qt.Horizontal
        ):

            return self.HEADERS[section]

        return None


    def data(
        self,
        index,
        role=Qt.DisplayRole
    ):

        if not index.isValid():

            return None


        row = self.rows[index.row()]


        if role == Qt.DisplayRole:

            values = [
                row["industry"],
                row["track"],
                row["spot"],
                row["car"],
                row["car_type"],
            ]

            return values[index.column()]


        #
        # Highlight occupied and empty spots.
        #
        # Do not set ForegroundRole here.
        # The application stylesheet controls
        # selected-row text color.
        #

        if role == Qt.BackgroundRole:

            if row["car_id"] is not None:

                return QBrush(
                    QColor("#dbeafe")
                )

            return QBrush(
                QColor("#f3f4f6")
            )


        return None


    def load_data(
        self,
        industry_id=None,
        track_id=None,
        occupied_only=False,
        empty_only=False,
    ):

        self.beginResetModel()

        self.rows = []


        with SessionLocal() as session:

            #
            # Eagerly load the entire relationship chain:
            #
            # Spot
            #   -> Track
            #       -> Industry
            #
            # and:
            #
            # Spot
            #   -> Car
            #
            # This prevents DetachedInstanceError after
            # the database session closes.
            #

            statement = (
                select(Spot)
                .options(
                    joinedload(
                        Spot.track
                    ).joinedload(
                        IndustryTrack.industry
                    ),

                    joinedload(
                        Spot.car
                    ),
                )
            )


            spots = (
                session.execute(
                    statement
                )
                .unique()
                .scalars()
                .all()
            )


            #
            # Sort while the session is still active.
            #

            spots.sort(
                key=lambda spot: (

                    (
                        spot.track.industry.name
                        if spot.track
                        and spot.track.industry
                        else ""
                    ),

                    (
                        spot.track.name
                        if spot.track
                        else ""
                    ),

                    spot.spot_number,

                )
            )


            for spot in spots:

                track = spot.track

                if track is None:

                    continue


                industry = track.industry

                if industry is None:

                    continue


                #
                # Industry filter
                #

                if (
                    industry_id is not None
                    and industry.id != industry_id
                ):

                    continue


                #
                # Track filter
                #

                if (
                    track_id is not None
                    and track.id != track_id
                ):

                    continue


                #
                # Car relationship was eagerly loaded.
                #

                car = spot.car


                #
                # Occupied-only filter
                #

                if (
                    occupied_only
                    and car is None
                ):

                    continue


                #
                # Empty-only filter
                #

                if (
                    empty_only
                    and car is not None
                ):

                    continue


                #
                # Car information
                #

                if car is not None:

                    car_name = (
                        f"{car.reporting_mark} "
                        f"{car.number}"
                    )


                    car_type = (
                        car.car_type
                        if car.car_type
                        else "Unknown"
                    )


                    car_id = car.id


                else:

                    car_name = "Empty"

                    car_type = ""

                    car_id = None


                #
                # Store only simple values in the
                # table model.
                #
                # This is important because the SQLAlchemy
                # session will close after this block.
                #

                self.rows.append(
                    {
                        "spot_id": spot.id,

                        "car_id": car_id,

                        "industry": industry.name,

                        "track": track.name,

                        "spot": spot.spot_number,

                        "car": car_name,

                        "car_type": car_type,
                    }
                )


        self.endResetModel()
