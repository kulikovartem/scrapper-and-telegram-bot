from src.scrapper.interfaces.update_sender_interface import UpdateSender
from typing import List, Tuple, Dict
import httpx
import logging
from src.server_settings import ServerSettings
from src.scrapper.interfaces.desc_maker_interface import DescMaker
from src.scrapper.services.desc_maker_service import DescMakerService
from src.scrapper.schemas.link_dto import LinkDTO

logger = logging.getLogger(__name__)
server_settings = ServerSettings()


class UpdateSenderToBot(UpdateSender):

    """
        Сервис для отправки обновлений боту.

        Этот класс реализует интерфейс `UpdateSender` и отвечает за отправку запросов с обновленной информацией
        по ссылкам в API бота.

        Атрибуты:
            _bot_ip (str): IP-адрес бота для отправки обновлений.
            _bot_port (int): Порт, на котором работает бот.
            _desc_maker (DescMaker): Экземпляр сервиса для формирования описаний.
            _base_url (str): URL, по которому осуществляется запрос.

        Методы:
            send_update_request(links_info: List[Tuple[LinkDTO, Dict[str, str]]]) -> None:
                Отправляет обновленные данные по ссылкам в API бота.

        Логирование:
            - Фиксирует успешные отправки запросов на обновление.
            - Фиксирует ошибки при отправке запросов.

        Пример использования:
            sender = UpdateSenderToBot()
            sender.send_update_request(list_of_updates)
    """

    _bot_ip: str = server_settings.BOT_IP
    _bot_port: int = server_settings.BOT_PORT
    _desc_maker: DescMaker = DescMakerService()

    def send_update_request(self, links_info: List[Tuple[LinkDTO, Dict[str, str]]]) -> None:
        """
        Отправляет запрос на обновление данных для каждой ссылки.

        Параметры:
            links_info (List[Tuple[LinkDTO, Dict[str, str]]]): Список ссылок и соответствующих данных для обновления.

        Логирование:
            - Записывает информацию о попытке отправки обновлений и возможные ошибки.
        """

        for pair in links_info:
            info = pair[1]
            payload = {
                "id": pair[0].tg_id,
                "url": pair[0].link,
                "description": self._desc_maker.make_desc(info),
                "tgChatIds": [str(pair[0].tg_id)],
            }
            try:
                with httpx.Client() as client:
                    client.post(self._base_url, json=payload)
                logger.info("Запрос на обновление отправлен", extra={"link": pair[0].link, "tg_id": pair[0].tg_id})
            except Exception as e:
                logger.error("Ошибка при отправке запроса для ссылки", extra={"link": pair[0].link, "error": str(e)})

    @property
    def _base_url(self) -> str:
        return f"http://{self._bot_ip}:{self._bot_port}/api/v1/updates"
