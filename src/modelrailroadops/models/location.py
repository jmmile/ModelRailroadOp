from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modelrailroadops.database.base import Base


class Location(Base):
    """A named operational place served by the railroad."""

    __tablename__ = "locations"

    __table_args__ = (
        UniqueConstraint("name", name="uq_location_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    location_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OTHER",
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    tracks: Mapped[list["LocationTrack"]] = relationship(
        "LocationTrack",
        back_populates="location",
        cascade="all, delete-orphan",
        order_by="LocationTrack.name",
    )

    industries: Mapped[list["Industry"]] = relationship(
        "Industry",
        back_populates="operating_location",
    )

    route_stops: Mapped[list["TrainRoute"]] = relationship(
        "TrainRoute",
        back_populates="operating_location",
    )

    cars: Mapped[list["Car"]] = relationship(
        "Car",
        back_populates="operating_location",
    )
