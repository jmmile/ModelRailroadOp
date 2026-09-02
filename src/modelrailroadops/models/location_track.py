from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modelrailroadops.database.base import Base


class LocationTrack(Base):
    """An operational track within a general railroad location."""

    __tablename__ = "location_tracks"

    __table_args__ = (
        UniqueConstraint(
            "location_id",
            "name",
            name="uq_location_track_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    track_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OTHER",
    )

    traffic_use: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="BOTH",
    )

    capacity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
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

    location: Mapped["Location"] = relationship(
        "Location",
        back_populates="tracks",
    )

    industry_tracks: Mapped[list["IndustryTrack"]] = relationship(
        "IndustryTrack",
        back_populates="operating_track",
    )

    route_stops: Mapped[list["TrainRoute"]] = relationship(
        "TrainRoute",
        back_populates="operating_track",
    )

    cars: Mapped[list["Car"]] = relationship(
        "Car",
        back_populates="operating_track",
    )
