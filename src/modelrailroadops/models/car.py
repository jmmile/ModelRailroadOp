from sqlalchemy import (
    ForeignKey,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

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
    # Car length in feet
    #
    # Used for spot restrictions
    # and operational validation.
    #

    length: Mapped[int | None] = mapped_column(
        nullable=True,
    )


    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )


    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )


    #
    # Assigned operating location
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


    #
    # Relationships
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