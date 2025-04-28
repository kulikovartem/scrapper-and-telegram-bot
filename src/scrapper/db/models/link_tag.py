from src.scrapper.db.config import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, PrimaryKeyConstraint


class LinkTag(Base):

    __tablename__ = "link_tag"

    link_id: Mapped[int] = mapped_column(ForeignKey("link_date.link_id", ondelete="CASCADE"), primary_key=True)
    tag: Mapped[str] = mapped_column(primary_key=True)

    link: Mapped["LinkDate"] = relationship("LinkDate", back_populates="tags")  #  type: ignore
