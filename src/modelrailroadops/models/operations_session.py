from datetime import (
    UTC,
    date,
    datetime,
)

from sqlalchemy import (
    Date,
    DateTime,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from modelrailroadops.database.base import Base


class OperationsSession(Base):

    __tablename__ = "operations_sessions"

    #
    # Session ID.
    #

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    #
    # Session name.
    #

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    #
    # Operating date.
    #

    session_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    #
    # Session status.
    #
    # Possible values:
    #
    #   PLANNED
    #   ACTIVE
    #   COMPLETED
    #   CANCELLED
    #

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PLANNED",
    )

    #
    # Optional notes.
    #

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    #
    # Creation timestamp.
    #

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
    )

    #
    # Completion timestamp.
    #

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    #
    # Waybills assigned to this Operations Session.
    #

    waybills: Mapped[list["Waybill"]] = relationship(
        "Waybill",
        back_populates="operations_session",
    )

    #
    # Actual physical car movement history.
    #
    # These are CarMovement records created when
    # a car is physically moved.
    #

    car_movements: Mapped[list["CarMovement"]] = relationship(
        "CarMovement",
        back_populates="operations_session",
    )

    #
    # Generated switch-list car moves.
    #
    # These are CarMove records describing the
    # planned/generated pickup and setout work
    # performed by trains.
    #

    car_moves: Mapped[list["CarMove"]] = relationship(
        "CarMove",
        back_populates="operations_session",
        cascade="all, delete-orphan",
    )

    #
    # Trains assigned to this Operations Session.
    #

    session_trains: Mapped[
        list["OperationsSessionTrain"]
    ] = relationship(
        "OperationsSessionTrain",
        back_populates="operations_session",
        cascade="all, delete-orphan",
    )
