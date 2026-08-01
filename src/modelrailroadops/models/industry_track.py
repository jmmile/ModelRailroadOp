from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modelrailroadops.database.base import Base


class IndustryTrack(Base):
    __tablename__ = "industry_tracks"

    id: Mapped[int] = mapped_column(primary_key=True)

    industry_id: Mapped[int] = mapped_column(
        ForeignKey("industries.id")
    )

    name: Mapped[str] = mapped_column(String(50))

    spots: Mapped[int]

    industry = relationship(
        "Industry",
        back_populates="tracks",
)