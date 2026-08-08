from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from modelrailroadops.database.base import Base



class CarMovement(Base):

    __tablename__ = "car_movements"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    car_id: Mapped[int] = mapped_column(
        ForeignKey("cars.id"),
        nullable=False,
    )


    from_location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )


    to_location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )


    movement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )


    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )


    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


    car: Mapped["Car"] = relationship(
        "Car",
        back_populates="movements",
    )