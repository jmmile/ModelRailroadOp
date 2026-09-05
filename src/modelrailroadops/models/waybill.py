from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
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
    from modelrailroadops.models.industry import Industry
    from modelrailroadops.models.industry_track import IndustryTrack
    from modelrailroadops.models.location import Location
    from modelrailroadops.models.location_track import LocationTrack
    from modelrailroadops.models.operations_session import OperationsSession
    from modelrailroadops.models.spot import Spot


class Waybill(Base):

    __tablename__ = "waybills"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    #
    # Car assigned to this waybill.
    #

    car_id: Mapped[int] = mapped_column(
        ForeignKey("cars.id"),
        nullable=False,
    )

    #
    # Operations Session.
    #
    # A Waybill may optionally be assigned to
    # an Operations Session.
    #

    operations_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("operations_sessions.id"),
        nullable=True,
    )

    #
    # Origin location.
    #

    origin_location: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    origin_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"),
        nullable=True,
    )

    origin_location_track_id: Mapped[int | None] = mapped_column(
        ForeignKey("location_tracks.id"),
        nullable=True,
    )

    origin_industry_id: Mapped[int | None] = mapped_column(
        ForeignKey("industries.id"),
        nullable=True,
    )

    origin_track_id: Mapped[int | None] = mapped_column(
        ForeignKey("industry_tracks.id"),
        nullable=True,
    )

    origin_spot_id: Mapped[int | None] = mapped_column(
        ForeignKey("spots.id"),
        nullable=True,
    )

    #
    # Destination.
    #

    destination_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"),
        nullable=True,
    )

    destination_location_track_id: Mapped[int | None] = mapped_column(
        ForeignKey("location_tracks.id"),
        nullable=True,
    )

    destination_industry_id: Mapped[int | None] = mapped_column(
        ForeignKey("industries.id"),
        nullable=True,
    )

    destination_track_id: Mapped[int | None] = mapped_column(
        ForeignKey("industry_tracks.id"),
        nullable=True,
    )

    destination_spot_id: Mapped[int | None] = mapped_column(
        ForeignKey("spots.id"),
        nullable=True,
    )

    #
    # Load and weight information for this movement.
    #

    load_state: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    commodity: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    cargo_weight_lbs: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    #
    # Waybill status.
    #

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACTIVE",
    )

    #
    # Optional operational notes.
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
    # Archive state.
    #

    archived: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    @property
    def gross_weight_lbs(self):
        """Return the car's gross weight for this Waybill in pounds."""

        if self.car is None or self.car.empty_weight_lbs is None:
            return None

        if self.load_state == "EMPTY":
            return self.car.empty_weight_lbs

        if self.load_state == "LOADED" and self.cargo_weight_lbs is not None:
            return self.car.empty_weight_lbs + self.cargo_weight_lbs

        return None

    @property
    def tonnage(self):
        """Return gross weight expressed as US short tons."""

        gross_weight_lbs = self.gross_weight_lbs

        if gross_weight_lbs is None:
            return None

        return gross_weight_lbs / 2000.0

    #
    # Relationships.
    #

    car: Mapped["Car"] = relationship(
        "Car",
        back_populates="waybills",
    )

    operations_session: Mapped[
        "OperationsSession | None"
    ] = relationship(
        "OperationsSession",
        back_populates="waybills",
    )

    origin_industry: Mapped[
        "Industry | None"
    ] = relationship(
        "Industry",
        foreign_keys=[origin_industry_id],
    )

    origin_track: Mapped[
        "IndustryTrack | None"
    ] = relationship(
        "IndustryTrack",
        foreign_keys=[origin_track_id],
    )

    origin_spot: Mapped[
        "Spot | None"
    ] = relationship(
        "Spot",
        foreign_keys=[origin_spot_id],
    )

    origin_operating_location: Mapped[
        "Location | None"
    ] = relationship(
        "Location",
        foreign_keys=[origin_location_id],
    )

    origin_operating_track: Mapped[
        "LocationTrack | None"
    ] = relationship(
        "LocationTrack",
        foreign_keys=[origin_location_track_id],
    )

    destination_operating_location: Mapped[
        "Location | None"
    ] = relationship(
        "Location",
        foreign_keys=[destination_location_id],
    )

    destination_operating_track: Mapped[
        "LocationTrack | None"
    ] = relationship(
        "LocationTrack",
        foreign_keys=[destination_location_track_id],
    )

    destination_industry: Mapped[
        "Industry | None"
    ] = relationship(
        "Industry",
        foreign_keys=[destination_industry_id],
    )

    destination_track: Mapped[
        "IndustryTrack | None"
    ] = relationship(
        "IndustryTrack",
        foreign_keys=[destination_track_id],
    )

    destination_spot: Mapped[
        "Spot | None"
    ] = relationship(
        "Spot",
        foreign_keys=[destination_spot_id],
    )

