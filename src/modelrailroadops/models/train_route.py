from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from modelrailroadops.database.base import Base


class TrainRoute(Base):
    """
    Represents one ordered stop on a Train route.

    A Train may have multiple TrainRoute records.
    The sequence field determines the order in which
    the train visits each location.

    Each route stop may optionally be associated with
    an Industry. The Industry provides a reliable database
    identity for the location while the location field
    remains available for general railroad locations such
    as staging yards.
    """

    __tablename__ = "train_routes"

    #
    # Primary key
    #

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    #
    # Train
    #

    train_id: Mapped[int] = mapped_column(
        ForeignKey(
            "trains.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    #
    # Stop sequence
    #
    # Lower numbers occur earlier in the route.
    #

    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    #
    # Route location
    #
    # This remains as text so general railroad locations
    # such as staging yards can be used.
    #

    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    #
    # Industry
    #
    # Optional. General railroad locations do not require
    # an Industry.
    #

    industry_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "industries.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    #
    # General operational location.
    #

    location_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "locations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    location_track_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "location_tracks.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    #
    # Optional description of the stop.
    #

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    #
    # Relationship back to Train.
    #

    train: Mapped["Train"] = relationship(
        "Train",
        back_populates="routes",
    )

    #
    # Relationship to Industry.
    #

    industry: Mapped["Industry | None"] = relationship(
        "Industry",
    )

    operating_location: Mapped["Location | None"] = relationship(
        "Location",
        back_populates="route_stops",
    )

    operating_track: Mapped["LocationTrack | None"] = relationship(
        "LocationTrack",
        back_populates="route_stops",
    )

    def __repr__(
        self,
    ):

        return (
            f"<TrainRoute("
            f"id={self.id}, "
            f"train_id={self.train_id}, "
            f"sequence={self.sequence}, "
            f"location='{self.location}', "
            f"industry_id={self.industry_id}"
            f")>"
        )
