from PySide6.QtCore import Qt, QAbstractTableModel

from modelrailroadops.services.industry_service import IndustryService



class IndustryTableModel(QAbstractTableModel):

    HEADERS = [
        "Name",
        "Railroad",
        "Location",
        "Tracks",
        "Spots",
        "Occupied",
        "Available",
        "Capacity",
        "Notes",
    ]


    def __init__(self):

        super().__init__()

        self.industries = []

        self.refresh()



    def refresh(self):

        self.beginResetModel()

        self.industries = (
            IndustryService.get_all()
        )

        self.endResetModel()



    def rowCount(
        self,
        parent=None
    ):

        return len(self.industries)



    def columnCount(
        self,
        parent=None
    ):

        return len(self.HEADERS)



    def headerData(
        self,
        section,
        orientation,
        role
    ):

        if role != Qt.DisplayRole:

            return None


        if orientation == Qt.Horizontal:

            return self.HEADERS[section]


        return section + 1



    def get_capacity_data(self, industry):

        total_spots = sum(
            len(track.spots)
            for track in industry.tracks
        )


        occupied = sum(
            1
            for track in industry.tracks
            for spot in track.spots
            if spot.car is not None
        )


        available = (
            total_spots - occupied
        )


        capacity = (
            round(
                occupied / total_spots * 100
            )
            if total_spots
            else 0
        )


        return (
            total_spots,
            occupied,
            available,
            capacity,
        )



    def data(
        self,
        index,
        role
    ):

        if not index.isValid():

            return None



        industry = self.industries[
            index.row()
        ]


        (
            total_spots,
            occupied,
            available,
            capacity,
        ) = self.get_capacity_data(
            industry
        )



        #
        # Visual Capacity Status
        #

        if role == Qt.ForegroundRole:

            if capacity >= 90:

                return Qt.red


            elif capacity >= 70:

                return Qt.darkYellow


            else:

                return Qt.darkGreen



        if role == Qt.DisplayRole:


            match index.column():

                case 0:

                    return industry.name


                case 1:

                    return industry.railroad


                case 2:

                    return industry.location


                case 3:

                    return ", ".join(
                        track.name
                        for track in sorted(
                            industry.tracks,
                            key=lambda t: t.name
                        )
                    )


                case 4:

                    return total_spots


                case 5:

                    return occupied


                case 6:

                    return available


                case 7:

                    return f"{capacity}%"


                case 8:

                    return industry.notes



        return None



    def get_industry(
        self,
        row
    ):

        if 0 <= row < len(self.industries):

            return self.industries[row]


        return None