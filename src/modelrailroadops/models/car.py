from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from modelrailroadops.database.base import Base


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)

    reporting_mark: Mapped[str] = mapped_column(String(10))
    number: Mapped[str] = mapped_column(String(10))
    owner: Mapped[str] = mapped_column(String(50))
    car_type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30))
    location: Mapped[str] = mapped_column(String(100))