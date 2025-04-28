from src.scrapper.db.config import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from sqlalchemy import ForeignKey, Index
from src.scrapper.db.models.link_filter import LinkFilter
from src.scrapper.db.models.link_tag import LinkTag


class LinkDate(Base):

    __tablename__ = "link_date"

    link_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    link: Mapped[str] = mapped_column(index=True)
    date: Mapped[str]

    filters: Mapped[List["LinkFilter"]] = relationship("LinkFilter", back_populates="link",
                                                       cascade="all, delete-orphan")
    tags: Mapped[List["LinkTag"]] = relationship("LinkTag", back_populates="link", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_linkdate_tg_id", "tg_id"),
        Index("idx_linkdate_link", "link", postgresql_using="hash"),
    )
