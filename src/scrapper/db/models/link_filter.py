from src.scrapper.db.config import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, PrimaryKeyConstraint


class LinkFilter(Base):

    __tablename__ = "link_filter"

    link_id: Mapped[int] = mapped_column(ForeignKey("link_date.link_id", ondelete="CASCADE"), primary_key=True)
    filter: Mapped[str] = mapped_column(primary_key=True)

    link: Mapped["LinkDate"] = relationship("LinkDate", back_populates="filters")  # type: ignore
