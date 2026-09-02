from sqlalchemy import ForeignKey, String

from sqlalchemy.orm import Mapped, mapped_column, relationship

from modelrailroadops.database.base import Base


class Car(Base):

    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    reporting_mark: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    number: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    owner: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    car_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    #
    # Car length in feet.
    #
    # Used for spot restrictions
    # and operational validation.
    #

    length: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    #
    # Permanent weight markings, stored in pounds.
    #
    # Empty weight corresponds to the railroad car's LT WT marking.
    # Load limit corresponds to its LD LMT marking.
    #

    empty_weight_lbs: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    load_limit_lbs: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    @property
    def maximum_gross_weight_lbs(self):
        """Return empty weight plus load limit when both are known."""

        if self.empty_weight_lbs is None or self.load_limit_lbs is None:
            return None

        return self.empty_weight_lbs + self.load_limit_lbs

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    #
    # Legacy location text.
    #
    # Structured location is represented by
    # industry_id, track_id, and spot_id.
    #

    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    #
    # Assigned operating location.
    #

    industry_id: Mapped[int | None] = mapped_column(
        ForeignKey("industries.id"),
        nullable=True,
    )

    track_id: Mapped[int | None] = mapped_column(
        ForeignKey("industry_tracks.id"),
        nullable=True,
    )

    spot_id: Mapped[int | None] = mapped_column(
        ForeignKey("spots.id"),
        nullable=True,
    )

    operating_location_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "locations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    operating_track_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "location_tracks.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    #
    # Relationships.
    #

    industry: Mapped["Industry"] = relationship(
        "Industry",
        back_populates="cars",
    )

    track: Mapped["IndustryTrack"] = relationship(
        "IndustryTrack",
        back_populates="cars",
    )

    spot: Mapped["Spot"] = relationship(
        "Spot",
        back_populates="car",
    )

    movements: Mapped[list["CarMovement"]] = relationship(
        "CarMovement",
        back_populates="car",
        cascade="all, delete-orphan",
    )

    waybills: Mapped[list["Waybill"]] = relationship(
        "Waybill",
        back_populates="car",
        cascade="all, delete-orphan",
    )

    operating_location: Mapped["Location | None"] = relationship(
        "Location",
        back_populates="cars",
    )

    operating_track: Mapped["LocationTrack | None"] = relationship(
        "LocationTrack",
        back_populates="cars",
    )
