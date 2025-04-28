import typing
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ("TGBotSettings",)


class TGBotSettings(BaseSettings):
    """
    Настройки Telegram-бота.

    Этот класс использует pydantic BaseSettings для автоматического считывания
    конфигурационных параметров из переменных окружения или файла .env. Он включает
    необходимые параметры для подключения к API Telegram, такие как api_id, api_hash и token.

    Атрибуты:
        debug (bool): Флаг режима отладки. По умолчанию False.
        api_id (int): Идентификатор API Telegram.
        api_hash (str): Хэш API Telegram.
        token (str): Токен бота Telegram.

    Конфигурация (model_config):
        - extra="ignore": Игнорирует дополнительные поля, отсутствующие в модели.
        - frozen=True: Экземпляр настроек становится неизменяемым после создания.
        - case_sensitive=False: Имена переменных окружения нечувствительны к регистру.
        - env_file: Путь к файлу .env, который находится в родительской директории.
        - env_prefix="BOT_": Префикс для переменных окружения.
    """
    debug: bool = Field(default=False)
    api_id: int = Field(...)
    api_hash: str = Field(...)
    token: str = Field(...)

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent / ".env",
        env_prefix="BOT_",
    )
