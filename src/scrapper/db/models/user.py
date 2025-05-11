from datetime import time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.scrapper.db.config import Base
from src.scrapper.db.models.link_date import LinkDate
from typing import List


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    time_push_up: Mapped[time | None] = mapped_column(default=None, nullable=True)

    links: Mapped[List["LinkDate"]] = relationship()
