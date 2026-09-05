from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from modelrailroadops.database.base import Base


if TYPE_CHECKING:
    from modelrailroadops.models.car import Car
    from modelrailroadops.models.operations_session import (
        OperationsSession,
    )
    from modelrailroadops.models.train import Train
    from modelrailroadops.models.waybill import Waybill


class CarMove(Base):
    """
    Records a car movement generated for an
    Operations Session.

    A CarMove represents one operating instruction
    for a railroad car performed by a specific Train.

    Move types:

        PICKUP
        SETOUT

    Move statuses:

        PENDING
        COMPLETED
    """

    __tablename__ = "car_moves"

    #
    # Car move ID.
    #

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    #
    # Operations Session.
    #

    operations_session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "operations_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    #
    # Train performing the movement.
    #

    train_id: Mapped[int] = mapped_column(
        ForeignKey(
            "trains.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    #
    # Car being moved.
    #

    car_id: Mapped[int] = mapped_column(
        ForeignKey(
            "cars.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    #
    # Waybill responsible for the movement.
    #

    waybill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "waybills.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    #
    # Route sequence where the movement occurs.
    #

    route_sequence: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    #
    # Movement type.
    #
    # Possible values:
    #
    #   PICKUP
    #   SETOUT
    #

    move_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    #
    # Execution status.
    #
    # Possible values:
    #
    #   PENDING
    #   COMPLETED
    #

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
    )

    #
    # Origin location for this individual move.
    #

    origin_location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    #
    # Destination location for this individual move.
    #

    destination_location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    #
    # Optional operating notes.
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
    # Relationships.
    #

    operations_session: Mapped[
        "OperationsSession"
    ] = relationship(
        "OperationsSession",
        back_populates="car_moves",
    )

    train: Mapped[
        "Train"
    ] = relationship(
        "Train",
    )

    car: Mapped[
        "Car"
    ] = relationship(
        "Car",
    )

    waybill: Mapped[
        "Waybill"
    ] = relationship(
        "Waybill",
    )