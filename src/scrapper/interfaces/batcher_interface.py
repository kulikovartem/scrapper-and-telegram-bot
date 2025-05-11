from typing import Protocol, List
from src.scrapper.schemas.link_dto import LinkDTO
from src.scrapper.interfaces.link_repo_interface import LinkRepo


class Batcher(Protocol):

    """
        Протокол для классов, реализующих пакетную обработку ссылок.

        Классы, реализующие этот протокол, должны предоставлять метод `batch_links`,
        который принимает список ссылок и репозиторий для их обновления.

        Методы:
            async batch_links(links: List[LinkDTO], repo: LinkRepo) -> None:
                Выполняет пакетную обработку переданных ссылок, обновляя их данные
                и передавая в последующую обработку.

        Параметры:
            links (List[LinkDTO]): Список объектов LinkDTO, содержащих информацию о ссылках.
            repo (LinkRepo): Интерфейс репозитория для работы с данными ссылок.

        Использование:
            Класс, реализующий данный протокол, должен переопределить метод `batch_links`
            для обработки ссылок в пакетах, например, обновляя их информацию в базе данных
            или отправляя на дальнейшую обработку.

        Пример:
            class MyBatcher(Batcher):
                async def batch_links(self, links: List[LinkDTO], repo: LinkRepo) -> None:
                    for link in links:
                        await repo.update_link(link)
    """

    async def batch_links(self, links: List[LinkDTO], repo: LinkRepo) -> None:
        pass

    def start_cron_scheduler(self) -> None:
        pass
