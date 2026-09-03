from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from modelrailroadops.models.operations_session import (
        OperationsSession,
    )
    from modelrailroadops.models.operations_session_train_locomotive import (
        OperationsSessionTrainLocomotive,
    )
    from modelrailroadops.models.train import (
        Train,
    )


class OperationsSessionTrain(
    Base
):
    """
    Associates a Train with an Operations Session.

    Each Train can only be assigned once to the
    same Operations Session.
    """

    __tablename__ = "operations_session_trains"

    __table_args__ = (
        UniqueConstraint(
            "operations_session_id",
            "train_id",
            name="uq_operations_session_train",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    operations_session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "operations_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    train_id: Mapped[int] = mapped_column(
        ForeignKey(
            "trains.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    operations_session: Mapped[
        "OperationsSession"
    ] = relationship(
        "OperationsSession",
        back_populates="session_trains",
    )

    train: Mapped[
        "Train"
    ] = relationship(
        "Train",
        back_populates="operations_sessions",
    )

    locomotives: Mapped[
        list["OperationsSessionTrainLocomotive"]
    ] = relationship(
        "OperationsSessionTrainLocomotive",
        back_populates="operations_session_train",
        cascade="all, delete-orphan",
        order_by=(
            "OperationsSessionTrainLocomotive.sequence"
        ),
    )