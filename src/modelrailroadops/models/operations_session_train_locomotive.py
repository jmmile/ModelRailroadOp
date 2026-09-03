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


class OperationsSessionTrainLocomotive(Base):
    """
    Associates a locomotive with a Train assignment
    for a specific Operations Session.

    The sequence field preserves locomotive order
    within the consist.
    """

    __tablename__ = "operations_session_train_locomotives"

    __table_args__ = (
        UniqueConstraint(
            "operations_session_train_id",
            "locomotive_id",
            name="uq_operations_session_train_locomotive",
        ),
        UniqueConstraint(
            "operations_session_train_id",
            "sequence",
            name="uq_operations_session_train_locomotive_sequence",
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

    locomotive_id: Mapped[int] = mapped_column(
        ForeignKey(
            "locomotives.id",
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
        back_populates="locomotives",
    )

    locomotive: Mapped[
        "Locomotive"
    ] = relationship(
        "Locomotive",
        back_populates="session_train_assignments",
    )