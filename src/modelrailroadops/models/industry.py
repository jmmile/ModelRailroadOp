from sqlalchemy import (
    ForeignKey,
    String,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from modelrailroadops.database.base import Base


class Industry(Base):
    """
    Represents a freight industry served by the railroad.

    Each Industry may be linked to a general operational Location.
    The linked Location is classified as INDUSTRY and is used by
    the broader location, routing, and track infrastructure.
    """

    __tablename__ = "industries"

    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uq_industry_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    railroad: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    operating_location_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "locations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    operating_location: Mapped["Location | None"] = relationship(
        "Location",
        back_populates="industries",
    )

    tracks: Mapped[list["IndustryTrack"]] = relationship(
        "IndustryTrack",
        back_populates="industry",
        cascade="all, delete-orphan",
        order_by="IndustryTrack.name",
    )

    cars: Mapped[list["Car"]] = relationship(
        "Car",
        back_populates="industry",
    )

    def __repr__(self):
        return (
            f"<Industry("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"railroad='{self.railroad}'"
            f")>"
        )