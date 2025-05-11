from pydantic import Field
from pydantic_settings import SettingsConfigDict, BaseSettings
from pathlib import Path
import typing


class ServerSettings(BaseSettings):
    """
    Настройки сервера для приложения.

    Этот класс использует pydantic BaseSettings для автоматического считывания
    конфигурационных параметров из переменных окружения или файла .env. Настройки
    включают параметры для подключения к серверу скраппера и серверу бота.

    Атрибуты:
        scrapper_ip (str): IP-адрес сервера скраппера.
        scrapper_port (int): Порт сервера скраппера.
        bot_ip (str): IP-адрес сервера бота.
        bot_port (int): Порт сервера бота.

    Конфигурация (model_config):
        - extra="ignore": Игнорирует дополнительные поля, отсутствующие в модели.
        - frozen=True: Экземпляр настроек является неизменяемым после создания.
        - case_sensitive=False: Имена переменных окружения нечувствительны к регистру.
        - env_file: Путь к файлу .env, расположенный в родительской директории от текущего файла.
        - env_prefix="SERVER_": Префикс для переменных окружения.
    """
    SCRAPPER_IP: str = Field(default="0.0.0.0")
    SCRAPPER_PORT: int = Field(default=8888)
    BOT_IP: str = Field(default="0.0.0.0")
    BOT_PORT: int = Field(default=7777)
    PUSH_TYPE: str = Field(default="KAFKA")

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent / ".serverenv",
        env_prefix="SERVER_",
    )
