from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modelrailroadops.database.base import Base


class IndustryTrack(Base):

    __tablename__ = "industry_tracks"


    __table_args__ = (
        UniqueConstraint(
            "industry_id",
            "name",
            name="uq_industry_track_name",
        ),
    )


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    industry_id: Mapped[int] = mapped_column(
        ForeignKey("industries.id"),
        nullable=False,
    )


    operating_track_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "location_tracks.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )


    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )


    # Parent industry
    industry = relationship(
        "Industry",
        back_populates="tracks",
    )


    operating_track = relationship(
        "LocationTrack",
        back_populates="industry_tracks",
    )


    # Individual spots on this track
    spots = relationship(
        "Spot",
        back_populates="track",
        cascade="all, delete-orphan",
        order_by="Spot.spot_number",
    )


    # Cars currently assigned to this track
    cars = relationship(
        "Car",
        back_populates="track",
    )
