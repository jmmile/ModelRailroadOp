from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from modelrailroadops.database.base import Base



class Industry(Base):
    __tablename__ = "industries"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))
    railroad: Mapped[str] = mapped_column(String(10))
    location: Mapped[str] = mapped_column(String(100))


    #
    # Legacy fields.
    # These will be removed after all UI has been migrated
    # to the IndustryTrack model.
    #
    track: Mapped[str] = mapped_column(String(50))
    spots: Mapped[int]
    
    #

    notes: Mapped[str] = mapped_column(String(500))
    
    tracks = relationship(
        "IndustryTrack",
        back_populates="industry",
        cascade="all, delete-orphan",
  )