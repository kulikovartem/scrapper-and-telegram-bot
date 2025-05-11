import logging
import asyncio
from src.scrapper.interfaces.link_repo_interface import LinkRepo
from src.scrapper.endpoints import db_settings
from src.scrapper.endpoints import REPO
from src.scrapper.interfaces.batcher_interface import Batcher
from src.scrapper.services.batch_links_service import BatchLinksService

logger = logging.getLogger(__name__)


class Scheduler:
    """
        Планировщик обработки ссылок.

        Этот класс отвечает за периодическое извлечение ссылок из базы данных, их обработку
        и последующее обновление информации о них. Если в базе данных отсутствуют ссылки для обработки,
        выполнение приостанавливается на 1 час перед повторной проверкой.

        Атрибуты:
            _page (int): Текущий номер страницы для пагинации.
            _page_size (int): Количество ссылок, загружаемых за один запрос.
            _repo (LinkRepo): Репозиторий для работы с хранилищем ссылок.
            _batcher (Batcher): Сервис для пакетной обработки ссылок.

        Методы:
            start(): Запускает бесконечный цикл планировщика, в котором ссылки извлекаются,
                     обрабатываются и обновляются. В случае отсутствия ссылок процесс засыпает на 1 час.
    """

    _page: int = 1
    _page_size: int = db_settings.PAGESIZE
    _repo: LinkRepo = REPO
    _batcher: Batcher = BatchLinksService()

    async def start(self) -> None:
        """
        Основной метод для запуска планировщика. Он периодически получает ссылки из базы данных,
        обрабатывает их и отправляет обновления. Если ссылки не найдены, метод ждет 1 час перед
        новой попыткой.

        Логирование:
            - Записывает начало и конец обработки ссылок.
        """
        self._batcher.start_cron_scheduler()
        while True:
            logger.info("Получение ссылок для обработки", extra={"page": self._page, "page_size": self._page_size})
            links = await self._repo.get_all(page=self._page, page_size=self._page_size)
            if links:
                await self._batcher.batch_links(links, self._repo)
                self._page += 1
            else:
                self._page = 1
                logger.info("Ссылки не найдены, ожидаем 1 час", extra={"page": self._page})
                await asyncio.sleep(3600)
