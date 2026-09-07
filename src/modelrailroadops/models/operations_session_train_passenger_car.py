from sqlalchemy import (
    ForeignKey,
    Integer,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from modelrailroadops.database.base import Base


class OperationsSessionTrainPassengerCar(Base):
    """
    Associates a passenger car with a Train assignment
    for a specific Operations Session.

    The sequence field preserves passenger car order
    within the consist.
    """

    __tablename__ = "operations_session_train_passenger_cars"

    __table_args__ = (
        UniqueConstraint(
            "operations_session_train_id",
            "passenger_car_id",
            name="uq_operations_session_train_passenger_car",
        ),
        UniqueConstraint(
            "operations_session_train_id",
            "sequence",
            name="uq_operations_session_train_passenger_car_sequence",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    operations_session_train_id: Mapped[int] = mapped_column(
        ForeignKey(
            "operations_session_trains.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    passenger_car_id: Mapped[int] = mapped_column(
        ForeignKey(
            "passenger_cars.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    operations_session_train: Mapped[
        "OperationsSessionTrain"
    ] = relationship(
        "OperationsSessionTrain",
        back_populates="passenger_cars",
    )

    passenger_car: Mapped[
        "PassengerCar"
    ] = relationship(
        "PassengerCar",
        back_populates="session_train_assignments",
    )