#```python
from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
)

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot


class IndustryTrackTableModel(QAbstractTableModel):
    """
    Table model for industries and their industry tracks.

    Every industry is displayed, including industries that
    currently have no tracks.

    Industries without tracks receive a special row with:

        Track Name = "No Tracks"
        Spots = 0
        Occupied = 0
        Available = 0

    The underlying track value for these rows is None.

    Industries are ordered with the most recently created
    industry first.
    """

    HEADERS = [
        "Industry",
        "Track Name",
        "Spots",
        "Occupied",
        "Available",
    ]

    def __init__(self):
        super().__init__()

        self.tracks = []

        self.refresh()

    #
    # Refresh
    #

    def refresh(self):
        """
        Reload all industries and tracks directly from
        the database.

        Every industry receives at least one row, even
        when it has no tracks.

        Industries are ordered by ID descending so the
        newest industry appears first.
        """

        self.beginResetModel()

        try:

            with SessionLocal() as session:

                industries = (
                    session.execute(
                        select(Industry)
                        .options(
                            selectinload(
                                Industry.tracks
                            )
                            .selectinload(
                                IndustryTrack.spots
                            )
                            .selectinload(
                                Spot.car
                            )
                        )
                        .order_by(
                            Industry.id.desc()
                        )
                    )
                    .scalars()
                    .all()
                )

                rows = []

                for industry in industries:

                    #
                    # Industry has no tracks.
                    #
                    # Still create a row so the industry
                    # can be selected and its first track
                    # can be added.
                    #

                    if not industry.tracks:

                        rows.append(
                            {
                                "industry_id": industry.id,
                                "industry_name": industry.name,
                                "industry": industry,
                                "track_id": None,
                                "track_name": "No Tracks",
                                "track": None,
                                "spot_total": 0,
                                "spot_occupied": 0,
                                "spot_available": 0,
                            }
                        )

                        continue

                    #
                    # Industry has one or more tracks.
                    #

                    sorted_tracks = sorted(
                        industry.tracks,
                        key=lambda item: (
                            item.name or ""
                        ).lower(),
                    )

                    for track in sorted_tracks:

                        spot_total = len(
                            track.spots
                        )

                        spot_occupied = sum(
                            1
                            for spot in track.spots
                            if spot.car is not None
                        )

                        spot_available = (
                            spot_total
                            - spot_occupied
                        )

                        rows.append(
                            {
                                "industry_id": industry.id,
                                "industry_name": industry.name,
                                "industry": industry,
                                "track_id": track.id,
                                "track_name": track.name,
                                "track": track,
                                "spot_total": spot_total,
                                "spot_occupied": spot_occupied,
                                "spot_available": spot_available,
                            }
                        )

                self.tracks = rows

        finally:

            self.endResetModel()

    #
    # Row count
    #

    def rowCount(
        self,
        parent=None,
    ):

        return len(
            self.tracks
        )

    #
    # Column count
    #

    def columnCount(
        self,
        parent=None,
    ):

        return len(
            self.HEADERS
        )

    #
    # Header data
    #

    def headerData(
        self,
        section,
        orientation,
        role,
    ):

        if role != Qt.DisplayRole:

            return None

        if orientation == Qt.Horizontal:

            if 0 <= section < len(
                self.HEADERS
            ):

                return self.HEADERS[
                    section
                ]

        elif orientation == Qt.Vertical:

            return section + 1

        return None

    #
    # Data
    #

    def data(
        self,
        index,
        role,
    ):

        if not index.isValid():

            return None

        row_number = index.row()

        if row_number < 0:

            return None

        if row_number >= len(
            self.tracks
        ):

            return None

        row = self.tracks[
            row_number
        ]

        #
        # Display data
        #

        if role == Qt.DisplayRole:

            column = index.column()

            if column == 0:

                return row[
                    "industry_name"
                ]

            if column == 1:

                return row[
                    "track_name"
                ]

            if column == 2:

                return row[
                    "spot_total"
                ]

            if column == 3:

                return row[
                    "spot_occupied"
                ]

            if column == 4:

                return row[
                    "spot_available"
                ]

        #
        # Alignment
        #

        if role == Qt.TextAlignmentRole:

            column = index.column()

            if column in (
                2,
                3,
                4,
            ):

                return (
                    Qt.AlignCenter
                    | Qt.AlignVCenter
                )

        return None

    #
    # Get industry for a row
    #

    def get_industry(
        self,
        row,
    ):

        if not (
            0 <= row < len(
                self.tracks
            )
        ):

            return None

        return self.tracks[
            row
        ].get(
            "industry"
        )

    #
    # Get track for a row
    #

    def get_track(
        self,
        row,
    ):

        if not (
            0 <= row < len(
                self.tracks
            )
        ):

            return None

        return self.tracks[
            row
        ].get(
            "track"
        )

    #
    # Get industry ID for a row
    #

    def get_industry_id(
        self,
        row,
    ):

        if not (
            0 <= row < len(
                self.tracks
            )
        ):

            return None

        return self.tracks[
            row
        ].get(
            "industry_id"
        )

    #
    # Get track ID for a row
    #

    def get_track_id(
        self,
        row,
    ):

        if not (
            0 <= row < len(
                self.tracks
            )
        ):

            return None

        return self.tracks[
            row
        ].get(
            "track_id"
        )
