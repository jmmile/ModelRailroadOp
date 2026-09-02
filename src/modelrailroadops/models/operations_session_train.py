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

    #
    # Primary key.
    #

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    #
    # Operations Session ID.
    #

    operations_session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "operations_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    #
    # Train ID.
    #

    train_id: Mapped[int] = mapped_column(
        ForeignKey(
            "trains.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    #
    # Operations Session relationship.
    #

    operations_session: Mapped[
        "OperationsSession"
    ] = relationship(
        "OperationsSession",
        back_populates="session_trains",
    )

    #
    # Train relationship.
    #

    train: Mapped[
        "Train"
    ] = relationship(
        "Train",
        back_populates="operations_sessions",
    )