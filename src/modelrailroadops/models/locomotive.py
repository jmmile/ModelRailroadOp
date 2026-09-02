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


class Locomotive(Base):
    """
    Represents a locomotive available for assignment
    to trains during operations sessions.
    """

    __tablename__ = "locomotives"

    __table_args__ = (
        UniqueConstraint(
            "reporting_mark",
            "number",
            name="uq_locomotive_reporting_mark_number",
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

    owner: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    locomotive_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Diesel",
    )

    horsepower: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

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
            f"<Locomotive("
            f"id={self.id}, "
            f"reporting_mark='{self.reporting_mark}', "
            f"number='{self.number}', "
            f"model='{self.model}'"
            f")>"
        )