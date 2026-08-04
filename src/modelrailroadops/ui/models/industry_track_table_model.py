from PySide6.QtCore import Qt, QAbstractTableModel

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.industry_track import IndustryTrack


class IndustryTrackTableModel(QAbstractTableModel):

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


    def refresh(self):

        self.beginResetModel()

        with SessionLocal() as session:

            self.tracks = (
                session.execute(
                    select(IndustryTrack)
                    .options(
                        selectinload(
                            IndustryTrack.industry
                        ),
                        selectinload(
                            IndustryTrack.spots
                        ),
                    )
                    .order_by(
                        IndustryTrack.industry_id,
                        IndustryTrack.name,
                    )
                )
                .scalars()
                .all()
            )


            # Detach safe copies
            for track in self.tracks:

                track.industry_name = (
                    track.industry.name
                    if track.industry
                    else ""
                )

                track.spot_total = len(
                    track.spots
                )

                track.spot_occupied = sum(
                    1
                    for spot in track.spots
                    if spot.car
                )

                track.spot_available = (
                    track.spot_total
                    -
                    track.spot_occupied
                )


        self.endResetModel()



    def rowCount(self, parent=None):

        return len(self.tracks)



    def columnCount(self, parent=None):

        return len(self.HEADERS)



    def headerData(
        self,
        section,
        orientation,
        role
    ):

        if (
            role == Qt.DisplayRole
            and orientation == Qt.Horizontal
        ):

            return self.HEADERS[section]

        return None



    def data(self, index, role):

        if not index.isValid():

            return None


        if role == Qt.DisplayRole:

            track = self.tracks[index.row()]


            if index.column() == 0:

                return track.industry_name


            if index.column() == 1:

                return track.name


            if index.column() == 2:

                return track.spot_total


            if index.column() == 3:

                return track.spot_occupied


            if index.column() == 4:

                return track.spot_available


        return None