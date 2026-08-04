from PySide6.QtCore import Qt, QAbstractTableModel

from modelrailroadops.services.industry_service import IndustryService


class IndustryTableModel(QAbstractTableModel):

    HEADERS = [
        "Name",
        "Railroad",
        "Location",
        "Tracks",
        "Spots",
        "Notes",
    ]

    def __init__(self):
        super().__init__()

        self.industries = []

        self.refresh()


    def refresh(self):

        self.beginResetModel()

        self.industries = IndustryService.get_all()

        self.endResetModel()


    def rowCount(self, parent=None):

        return len(self.industries)


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


    def data(
        self,
        index,
        role
    ):

        if not index.isValid():
            return None


        industry = self.industries[index.row()]


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
                    return sum(
                        len(track.spots)
                        for track in industry.tracks
                    )

                case 5:
                    return industry.notes


        return None


    def get_industry(self, row):

        if 0 <= row < len(self.industries):

            return self.industries[row]

        return None