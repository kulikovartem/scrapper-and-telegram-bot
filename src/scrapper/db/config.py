from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker, AsyncSession
from src.scrapper.db.db_settings import DBSettings

db_settings = DBSettings()

engine = create_async_engine(
    url=db_settings.database_url_asyncpg,
    echo=True,
)

session_factory = async_sessionmaker(engine)


class Base(DeclarativeBase):

    def __repr__(self):     # type: ignore
        columns = [col.name for col in self.__table__.columns]
        values = ", ".join(f"{col}={getattr(self, col)!r}" for col in columns)
        return f"<{self.__class__.__name__}({values})>"
