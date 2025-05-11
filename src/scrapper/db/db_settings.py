import typing
from pydantic import Field
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=6577)
    PASS: str = Field(default="tbank")
    USER: str = Field(default="tbank")
    NAME: str = Field(default="tbank")
    PAGESIZE: int = Field(default=50)
    ACCESS_TYPE: str = Field(default="ORM")

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent.parent.parent / ".dbenv",
        env_prefix="DB_",
    )

    @property
    def database_url_asyncpg(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASS}@{self.HOST}:{self.PORT}/{self.NAME}"
