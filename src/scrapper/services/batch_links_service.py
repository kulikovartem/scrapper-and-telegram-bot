from typing import List, Tuple, Dict
from src.scrapper.schemas.link_dto import LinkDTO
from src.scrapper.client_factory import ClientFactory
from src.scrapper.url_type_definer import URLTypeDefiner
import logging
from concurrent.futures import ThreadPoolExecutor
from src.scrapper.interfaces.batcher_interface import Batcher
from src.server_settings import ServerSettings
from src.scrapper.interfaces.link_repo_interface import LinkRepo
from src.scrapper.interfaces.update_sender_interface import UpdateSender
from src.scrapper.services.update_sender_to_bot import UpdateSenderToBot

logger = logging.getLogger(__name__)
server_settings = ServerSettings()  # type:ignore


class BatchLinksService(Batcher):

    """
        Сервис для пакетной обработки ссылок.

        Этот класс реализует интерфейс `Batcher` и предназначен для обработки списка ссылок в пакетном режиме.
        Основные шаги обработки:

        1. Разделяет список ссылок на части.
        2. Определяет тип ссылки и получает обновленные данные.
        3. Обновляет информацию в базе данных при необходимости.
        4. Отправляет обновленные данные в API бота через `_update_sender`.

        Атрибуты:
            _bot_ip (str): IP-адрес бота для отправки обновлений.
            _bot_port (int): Порт, на котором работает бот.
            _update_sender (UpdateSender): Экземпляр сервиса для отправки обновлений.

        Методы:
            async batch_links(links: List[LinkDTO], repo: LinkRepo) -> None:
                Выполняет пакетную обработку ссылок:
                - Делит список ссылок на подсписки.
                - Определяет тип каждой ссылки и извлекает информацию.
                - Сравнивает полученные данные с текущими, обновляет их в базе, если изменились.
                - Отправляет обновления в API бота.

        Логирование:
            - Записывает успешные обновления ссылок.
            - Фиксирует ошибки при получении информации.
            - Фиксирует ошибки при отправке запросов на обновление.

        Пример использования:
            batcher = BatchLinksService()
            await batcher.batch_links(list_of_links, link_repository)
        """

    _bot_ip: str = server_settings.BOT_IP
    _bot_port: int = server_settings.BOT_PORT
    _update_sender: UpdateSender = UpdateSenderToBot()

    async def batch_links(self, links: List[LinkDTO], repo: LinkRepo) -> None:
        """
        Обрабатывает ссылки в пакетах. Разделяет список ссылок на более мелкие части и для каждой ссылки
        получает информацию, обновляет данные в базе и готовит информацию для отправки.

        Параметры:
            links (List[LinkDTO]): Список объектов с данными ссылок для обработки.

        Логирование:
            - Записывает успешные и ошибочные обработки ссылок.
        """
        chunk_size = max(1, len(links) // 4)
        chunks = [links[i:i + chunk_size] for i in range(0, len(links), chunk_size)]
        to_send = []

        for lst in chunks:
            links_with_updates = []
            for link in lst:
                url_type = URLTypeDefiner.define(link.link)
                client = ClientFactory.create_client(url_type)
                try:
                    info = await client.get_info_by_url_with_filters(link.link, link.filters)
                    date = info["date"]
                    if date != link.date:
                        links_with_updates.append((link, info))
                        await repo.change_date(int(link.link_id), str(date))
                        logger.info("Обновлена информация для ссылки", extra={"link": link.link, "new_date": date})
                except Exception as e:
                    logger.error("Ошибка при получении информации для ссылки",
                                 extra={"link": link.link, "error": str(e)})
            to_send.append(links_with_updates)

        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(self._update_sender.send_update_request, to_send)
