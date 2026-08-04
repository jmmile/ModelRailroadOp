from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modelrailroadops.database.base import Base


class Spot(Base):

    __tablename__ = "spots"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    track_id: Mapped[int] = mapped_column(
        ForeignKey("industry_tracks.id"),
        nullable=False,
    )


    spot_number: Mapped[int] = mapped_column(
        nullable=False,
    )


    # Future operational restrictions
    max_length: Mapped[int | None] = mapped_column(
        nullable=True
    )


    allowed_car_type: Mapped[str | None] = mapped_column(
        nullable=True
    )


    # Track this spot belongs to
    track = relationship(
        "IndustryTrack",
        back_populates="spots",
    )


    # Car currently occupying this spot
    # One spot can contain one car
    car = relationship(
        "Car",
        back_populates="spot",
        uselist=False,
    )