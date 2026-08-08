from sqlalchemy import (
    Boolean,
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


class Spot(Base):

    __tablename__ = "spots"


    #
    # Primary key
    #

    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    #
    # Parent industry track
    #

    track_id: Mapped[int] = mapped_column(
        ForeignKey("industry_tracks.id"),
        nullable=False,
    )


    #
    # Physical spot number
    #

    spot_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


    #
    # Spot identification
    #

    name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )


    description: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )


    #
    # Operational restrictions
    #

    max_length: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )


    allowed_car_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )


    allowed_owner: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )


    hazardous_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


    #
    # Loading restrictions
    #

    load_only: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )


    empty_only: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )


    #
    # Additional notes
    #

    notes: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )


    #
    # Relationships
    #

    track = relationship(
        "IndustryTrack",
        back_populates="spots",
    )


    #
    # Car currently occupying this spot
    #
    # One spot contains one car.
    #
    # joined loading prevents a detached Spot from
    # attempting to lazy-load its car later.
    #

    car = relationship(
        "Car",
        back_populates="spot",
        uselist=False,
        lazy="joined",
    )


    def __repr__(self):

        return (
            f"<Spot "
            f"{self.spot_number} "
            f"Track={self.track_id}>"
        )
