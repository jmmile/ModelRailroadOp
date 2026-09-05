from sqlalchemy import (
    Integer,
    String,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from modelrailroadops.database.base import Base


class PassengerCar(Base):
    """
    Represents passenger equipment available for assignment
    to passenger trains.

    Passenger cars are maintained separately from freight cars
    and do not participate in freight Waybills, Car Moves,
    or Switch Lists.
    """

    __tablename__ = "passenger_cars"

    __table_args__ = (
        UniqueConstraint(
            "reporting_mark",
            "number",
            name="uq_passenger_car_reporting_mark_number",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    reporting_mark: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    number: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    owner: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    equipment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    #
    # Passenger car length in feet.
    #

    length: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="AVAILABLE",
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    def __repr__(self):
        return (
            f"<PassengerCar("
            f"id={self.id}, "
            f"reporting_mark='{self.reporting_mark}', "
            f"number='{self.number}', "
            f"equipment_type='{self.equipment_type}'"
            f")>"
        )