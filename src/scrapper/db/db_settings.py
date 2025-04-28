import typing
from pydantic import Field
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    DB_HOST: str = Field(default="0.0.0.0")
    DB_PORT: int = Field(default=6577)
    DB_PASS: str = Field(default="tbank")
    DB_USER: str = Field(default="tbank")
    DB_NAME: str = Field(default="tbank")
    DB_PAGESIZE: int = Field(default=50)
    DB_SERVICE_TYPE: str = Field(default="SQL")

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent.parent.parent / ".dbenv",
        env_prefix="DB_",
    )

    @property
    def database_url_asyncpg(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
