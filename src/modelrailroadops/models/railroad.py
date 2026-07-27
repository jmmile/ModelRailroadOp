from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from modelrailroadops.database.base import Base


class Railroad(Base):
    __tablename__ = "railroads"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    scale: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    era: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )