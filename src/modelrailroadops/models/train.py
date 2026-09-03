from datetime import time
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import (
    Boolean,
    Integer,
    String,
    Time,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from modelrailroadops.database.base import Base

if TYPE_CHECKING:
    from modelrailroadops.models.operations_session_train import (
        OperationsSessionTrain,
    )
    from modelrailroadops.models.train_route import TrainRoute


class Train(Base):
    """
    Represents a railroad train used by the
    Model Railroad Operations system.

    A Train defines the permanent operating
    definition of a train.

    Train routes and Operations Session
    assignments are handled separately.
    """

    __tablename__ = "trains"

    TRAIN_TYPE_CHOICES: ClassVar[tuple[tuple[str, str | None], ...]] = (
        ("Local Freight", "L"),
        ("Through Freight", "M"),
        ("Yard", "Y"),
        ("Passenger", "P"),
        ("Mixed", None),
        ("Intermodal", "I"),
        ("Bulk", "B"),
        ("Extra Movement", "X"),
    )

    TRAIN_TYPE_PREFIXES: ClassVar[dict[str, str]] = {
        "local freight": "L",
        "through freight": "M",
        "manifest": "M",
        "manifest freight": "M",
        "yard": "Y",
        "passenger": "P",
        "intermodal": "I",
        "bulk": "B",
        "extra": "X",
        "extra movement": "X",
    }

    #
    # Primary key
    #

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    #
    # Train number
    #
    # Stored as text so train numbers such as
    # 101, 101A, or X101 can be supported.
    #

    number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    #
    # Train name
    #

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    #
    # Train type
    #
    # Examples:
    #
    #   Local Freight
    #   Through Freight
    #   Yard
    #   Intermodal
    #   Bulk
    #   Passenger
    #   Mixed
    #   Extra Movement
    #

    train_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    @classmethod
    def build_symbol(cls, number, train_type):
        """Return the operating symbol produced by type prefix + number."""

        number_text = str(number or "").strip()
        type_text = str(train_type or "").strip().casefold()
        prefix = cls.TRAIN_TYPE_PREFIXES.get(type_text, "")

        if not number_text:
            return ""

        # A leading letter means the user supplied a complete railroad
        # symbol already (for example L400 or X101). Do not prepend the
        # selected Train Type and produce invalid values such as YL400.
        if number_text[0].isalpha():
            return number_text

        return f"{prefix}{number_text}"

    @property
    def symbol(self):
        return self.build_symbol(self.number, self.train_type)

    #
    # Description
    #

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    #
    # Origin
    #

    origin: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    #
    # Destination
    #

    destination: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    #
    # Direction
    #
    # Examples:
    #
    #   Eastbound
    #   Westbound
    #   Northbound
    #   Southbound
    #

    direction: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    #
    # Priority
    #
    # Lower numbers can be used to represent
    # higher-priority trains.
    #
    # Example:
    #
    #   1 = Highest priority
    #   2 = Second priority
    #   3 = Third priority
    #

    priority: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    #
    # Operating limits
    #
    # These define the maximum planned train size.
    # A null value means no limit has been defined.
    #

    maximum_cars: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    maximum_tonnage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    #
    # Operating days
    #
    # Initially stored as readable text.
    #
    # Examples:
    #
    #   DAILY
    #   MON,TUE,WED,THU,FRI
    #   SAT,SUN
    #

    operating_days: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    #
    # Scheduled departure time
    #

    scheduled_departure: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    #
    # Scheduled arrival time
    #

    scheduled_arrival: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    #
    # Active
    #

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    #
    # Train route stops.
    #
    # Routes are maintained separately from the
    # basic Train record and are ordered by the
    # TrainRoute.sequence field.
    #

    routes: Mapped[list["TrainRoute"]] = relationship(
        "TrainRoute",
        back_populates="train",
        cascade="all, delete-orphan",
        order_by="TrainRoute.sequence",
    )

    #
    # Operations Sessions using this train.
    #

    operations_sessions: Mapped[
        list["OperationsSessionTrain"]
    ] = relationship(
        "OperationsSessionTrain",
        back_populates="train",
        cascade="all, delete-orphan",
    )

    def __repr__(
        self,
    ):

        return (
            f"<Train("
            f"id={self.id}, "
            f"number='{self.number}', "
            f"name='{self.name}'"
            f")>"
        )