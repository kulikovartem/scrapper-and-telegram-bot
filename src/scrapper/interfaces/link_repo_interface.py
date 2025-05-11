from typing import Protocol, List
from src.scrapper.schemas.list_links_response import ListLinksResponse
from src.scrapper.schemas.link_response import LinkResponse
from src.scrapper.schemas.link_dto import LinkDTO
import datetime


class LinkRepo(Protocol):
    """
    Протокол для репозитория ссылок.

    Этот протокол определяет интерфейс для работы с хранилищем ссылок, отслеживаемых пользователями в рамках Telegram-чата.
    Он включает методы для регистрации чатов, добавления, удаления и получения списка ссылок, а также для управления тегами и датами обновлений.

    Методы:
        register(tg_chat_id: int) -> None:
            Регистрирует новый чат в системе по указанному идентификатору.

        delete_by_tg_id(tg_chat_id: int) -> None:
            Удаляет все данные, связанные с указанным идентификатором чата.

        list(tg_chat_id: int, page: int, page_size: int) -> ListLinksResponse:
            Возвращает список ссылок, отслеживаемых указанным чатом, с учетом пагинации.

        add(resp: LinkResponse, date: str) -> None:
            Добавляет новую ссылку в репозиторий с указанием даты последнего обновления.

        delete(tg_chat_id: int, link: str) -> LinkResponse:
            Удаляет указанную ссылку для конкретного чата и возвращает удаленный объект ссылки.

        get_all(page: int, page_size: int) -> List[LinkDTO]:
            Возвращает все данные репозитория с пагинацией, сгруппированные по идентификатору чата.

        delete_tag(tg_id: int, link: str, tag: str) -> None:
            Удаляет указанный тег для ссылки в рамках чата.

        add_tag(tg_id: int, link: str, tag: str) -> None:
            Добавляет указанный тег к ссылке в рамках чата.

        change_date(link_id: int, date: str) -> None:
            Обновляет дату для конкретной ссылки по ее идентификатору.

    Атрибуты:
        Протокол описывает базовый интерфейс для работы с хранилищем ссылок и не предоставляет конкретной реализации.
    """

    async def register(self, tg_id: int) -> None:
        """
        Регистрирует чат с заданным идентификатором в системе.

        Args:
            tg_id (int): Идентификатор чата в Telegram.
        """
        pass

    async def delete_by_tg_id(self, tg_id: int) -> None:
        """
        Удаляет все данные, связанные с чатом, по заданному идентификатору.

        Args:
            tg_id (int): Идентификатор чата в Telegram.
        """
        pass

    async def list(self, tg_id: int, page: int, page_size: int) -> ListLinksResponse:
        """
        Возвращает список ссылок, отслеживаемых чатом, с поддержкой пагинации.

        Args:
            tg_id (int): Идентификатор чата в Telegram.
            page (int): Номер страницы (для пагинации).
            page_size (int): Размер страницы (количество ссылок на страницу).

        Returns:
            ListLinksResponse: Объект, содержащий список ссылок и общее количество.
        """
        pass

    async def add(self, resp: LinkResponse, date: str) -> None:
        """
        Добавляет новую ссылку с датой обновления в репозиторий.

        Args:
            resp (LinkResponse): Объект, представляющий информацию о ссылке.
            date (str): Дата обновления ссылки в строковом формате.
        """
        pass

    async def delete(self, tg_chat_id: int, link: str) -> LinkResponse:
        """
        Удаляет ссылку для заданного чата и возвращает объект удаленной ссылки.

        Args:
            tg_chat_id (int): Идентификатор чата Telegram.
            link (str): URL ссылки, которую нужно удалить.

        Returns:
            LinkResponse: Объект, представляющий удаленную ссылку.
        """
        pass

    async def get_all(self, page: int, page_size: int) -> List[LinkDTO]:
        """
        Возвращает все данные репозитория с пагинацией.

        Args:
            page (int): Номер страницы (для пагинации).
            page_size (int): Размер страницы (количество ссылок на страницу).

        Returns:
            List[LinkDTO]: Список объектов LinkDTO, представляющих все ссылки в репозитории.
        """
        pass

    async def delete_tag(self, tg_id: int, link: str, tag: str) -> None:
        """
        Удаляет указанный тег для ссылки в рамках чата.

        Args:
            tg_id (int): Идентификатор чата Telegram.
            link (str): URL ссылки, для которой нужно удалить тег.
            tag (str): Тег, который нужно удалить.
        """
        pass

    async def add_tag(self, tg_id: int, link: str, tag: str) -> None:
        """
        Добавляет указанный тег к ссылке в рамках чата.

        Args:
            tg_id (int): Идентификатор чата Telegram.
            link (str): URL ссылки, к которой нужно добавить тег.
            tag (str): Тег, который нужно добавить.
        """
        pass

    async def change_date(self, link_id: int, date: str) -> None:
        """
        Обновляет дату для указанной ссылки.

        Args:
            link_id (int): Идентификатор ссылки.
            date (str): Новая дата, которую нужно установить для ссылки.
        """
        pass

    async def change_time_push_up(self, tg_id: int, time_str: str | None) -> None:
        pass

    async def get_time_push_up(self, tg_id: int) -> datetime.time | None:
        pass
