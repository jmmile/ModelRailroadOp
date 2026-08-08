from PySide6.QtCore import (
    QAbstractTableModel,
    Qt,
)

from modelrailroadops.database.database import SessionLocal

from modelrailroadops.models.car_movement import CarMovement
from modelrailroadops.models.car import Car



class CarHistoryTableModel(QAbstractTableModel):
    """
    Table model for displaying car movement history.
    """


    HEADERS = [
        "Timestamp",
        "Car",
        "Movement",
        "From Location",
        "To Location",
        "Notes",
    ]


    def __init__(self, parent=None):

        super().__init__(parent)

        self.rows = []

        self.load_data()



    def rowCount(self, parent=None):

        return len(self.rows)



    def columnCount(self, parent=None):

        return len(self.HEADERS)



    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():

            return None


        if role == Qt.DisplayRole:

            row = self.rows[index.row()]

            column = index.column()


            values = [

                row["timestamp"],

                row["car"],

                row["movement_type"],

                row["from_location"],

                row["to_location"],

                row["notes"],

            ]


            return values[column]


        return None



    def headerData(
        self,
        section,
        orientation,
        role=Qt.DisplayRole
    ):

        if role == Qt.DisplayRole:

            if orientation == Qt.Horizontal:

                return self.HEADERS[section]


        return None



    def load_data(self, car_id=None):

        self.beginResetModel()


        self.rows = []


        with SessionLocal() as session:


            query = (
                session.query(CarMovement)
                .join(Car)
                .order_by(
                    CarMovement.timestamp.desc()
                )
            )


            if car_id is not None:

                query = query.filter(
                    CarMovement.car_id == car_id
                )


            movements = query.all()



            for movement in movements:


                car = movement.car


                self.rows.append(

                    {

                        "timestamp": (
                            movement.timestamp
                            .strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        ),


                        "car": (
                            f"{car.reporting_mark} "
                            f"{car.number}"
                        ),


                        "movement_type": (
                            movement.movement_type
                        ),


                        "from_location": (
                            movement.from_location
                            or ""
                        ),


                        "to_location": (
                            movement.to_location
                            or ""
                        ),


                        "notes": (
                            movement.notes
                            or ""
                        ),

                    }

                )


        self.endResetModel()