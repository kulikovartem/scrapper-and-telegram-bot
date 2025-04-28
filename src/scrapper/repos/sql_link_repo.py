from src.scrapper.db.config import session_factory
from src.scrapper.exceptions.chat_is_not_registered_exception import ChatIsNotRegisteredException
from src.scrapper.exceptions.already_registered_exception import AlreadyRegisteredChatException
from src.scrapper.exceptions.tag_already_exists_exception import TagAlreadyExistsException
from src.scrapper.exceptions.url_is_already_followed_exception import UrlIsAlreadyFollowed
from src.scrapper.exceptions.link_is_not_found_exception import LinkIsNotFoundException
from src.scrapper.exceptions.link_with_tag_is_not_found import LinkWithTagIsNotFound
from src.scrapper.schemas.link_response import LinkResponse
from src.scrapper.schemas.list_links_response import ListLinksResponse
from src.scrapper.schemas.link_dto import LinkDTO
from pydantic import HttpUrl
from sqlalchemy.sql import text
from typing import List
import logging
from src.scrapper.interfaces.link_repo_interface import LinkRepo

logger = logging.getLogger(__name__)


class SqlLinkRepo(LinkRepo):

    """
        Репозиторий для работы с объектами Link и User в базе данных.
        Обрабатывает операции регистрации, удаления, добавления и получения данных ссылок, а также операций с тегами.

        Методы:
            - register: Регистрирует нового пользователя по его tg_id.
            - delete_by_tg_id: Удаляет пользователя по tg_id.
            - list: Получает список ссылок для пользователя с указанным tg_id.
            - add: Добавляет новую ссылку для пользователя.
            - delete: Удаляет ссылку для пользователя.
            - get_all: Получает все ссылки с пагинацией.
            - delete_tag: Удаляет тег из ссылки для пользователя.
            - add_tag: Добавляет новый тег для указанной ссылки пользователя.
            - change_date: Изменяет дату для указанной ссылки.
    """

    async def register(self, tg_id: int) -> None:

        """
        Регистрирует нового пользователя с указанным tg_id, если он еще не зарегистрирован.

        Параметры:
            tg_id (int): Идентификатор чата в Telegram.

        Исключения:
            AlreadyRegisteredChatException: Если пользователь уже зарегистрирован.
        """

        async with session_factory() as session:
            async with session.begin():
                logger.info("register_start", extra={"tg_id": tg_id})
                result = await session.execute(text("SELECT id FROM users WHERE id = :tg_id"), {"tg_id": tg_id})
                user = result.scalar()

                if user is None:
                    await session.execute(text("INSERT INTO users (id) VALUES (:tg_id)"), {"tg_id": tg_id})
                    logger.info("user_registered", extra={"tg_id": tg_id})
                else:
                    logger.error("chat_already_registered", extra={"tg_id": tg_id})
                    raise AlreadyRegisteredChatException(f"Чат {tg_id} уже зарегистрирован")
        logger.info("register_end", extra={"tg_id": tg_id})

    async def delete_by_tg_id(self, tg_id: int) -> None:

        """
        Удаляет пользователя по его tg_id.

        Параметры:
            tg_id (int): Идентификатор чата в Telegram.

        Исключения:
            ChatIsNotRegisteredException: Если пользователь не найден в базе данных.
        """

        async with session_factory() as session:
            async with session.begin():
                logger.info("delete_start", extra={"tg_id": tg_id})
                result = await session.execute(text("SELECT id FROM users WHERE id = :tg_id"), {"tg_id": tg_id})
                user = result.scalar()

                if user:
                    await session.execute(text("DELETE FROM users WHERE id = :tg_id"), {"tg_id": tg_id})
                    logger.info("delete_start", extra={"tg_id": tg_id})
                else:
                    logger.error("chat_not_found", extra={"tg_id": tg_id})
                    raise ChatIsNotRegisteredException(f"Чат {tg_id} не зарегистрирован")
        logger.info("delete_end", extra={"tg_id": tg_id})

    async def list(self, tg_id: int, page: int, page_size: int = 50) -> ListLinksResponse:

        """
        Получает список ссылок для пользователя с указанным tg_id с пагинацией.

        Параметры:
            tg_id (int): Идентификатор чата в Telegram.
            page (int): Номер страницы.
            page_size (int): Количество ссылок на одной странице.

        Возвращает:
            ListLinksResponse: Ответ с данными о ссылках пользователя.

        Исключения:
            ChatIsNotRegisteredException: Если пользователь не найден в базе данных.
        """

        logger.info("list_start", extra={"tg_id": tg_id, "page": page, "page_size": page_size})
        async with session_factory() as session:
            async with session.begin():
                user_exists = await session.execute(
                    text("SELECT 1 FROM users WHERE id = :tg_id"),
                    {"tg_id": tg_id}
                )
                if user_exists.scalar_one_or_none() is None:
                    logger.error("chat_not_found", extra={"tg_id": tg_id})
                    raise ChatIsNotRegisteredException(f"Чат {tg_id} не зарегистрирован")

                result = await session.execute(
                    text("""
                        SELECT ld.link_id, ld.link, 
                               COALESCE(array_agg(DISTINCT lf.filter) FILTER (WHERE lf.filter IS NOT NULL), '{}') AS filters,
                               COALESCE(array_agg(DISTINCT lt.tag) FILTER (WHERE lt.tag IS NOT NULL), '{}') AS tags
                        FROM link_date ld
                        LEFT JOIN link_filter lf ON ld.link_id = lf.link_id
                        LEFT JOIN link_tag lt ON ld.link_id = lt.link_id
                        WHERE ld.tg_id = :tg_id
                        GROUP BY ld.link_id, ld.link
                        LIMIT :limit OFFSET :offset
                    """),
                    {
                        "tg_id": tg_id,
                        "limit": page_size,
                        "offset": (page - 1) * page_size,
                    }
                )
                links = result.fetchall()
                logger.info("list_end", extra={"tg_id": tg_id, "links_count": len(links)})
                return ListLinksResponse(
                    links=[
                        LinkResponse(
                            id=link.link_id,
                            url=HttpUrl(link.link),
                            filters=link.filters if isinstance(link.filters, list) else [],
                            tags=link.tags if isinstance(link.tags, list) else [],
                        )
                        for link in links
                    ],
                    size=len(links)
                )

    async def add(self, resp: LinkResponse, date: str) -> None:

        """
        Добавляет новую ссылку для пользователя.

        Параметры:
            resp (LinkResponse): Данные о ссылке.
            date (str): Дата добавления ссылки.

        Исключения:
            ChatIsNotRegisteredException: Если пользователь не найден в базе данных.
            UrlIsAlreadyFollowed: Если ссылка уже отслеживается.
        """

        logger.info("add_start", extra={"tg_id": resp.id, "url": resp.url})
        async with session_factory() as session:
            async with session.begin():
                result = await session.execute(text("SELECT id FROM users WHERE id = :tg_id"), {"tg_id": resp.id})
                user = result.scalar()
                if not user:
                    logger.error("chat_not_found", extra={"tg_id": resp.id})
                    raise ChatIsNotRegisteredException(f"Чат {resp.id} не зарегистрирован")

                result = await session.execute(
                    text("SELECT link_id FROM link_date WHERE tg_id = :tg_id AND link = :link"),
                    {"tg_id": resp.id, "link": str(resp.url)}
                )
                if result.scalar():
                    logger.error("url_already_followed", extra={"tg_id": resp.id, "url": resp.url})
                    raise UrlIsAlreadyFollowed(f"Ссылка {resp.url} уже отслеживается")

                result = await session.execute(
                    text("INSERT INTO link_date (tg_id, link, date) VALUES (:tg_id, :link, :date) RETURNING link_id"),
                    {"tg_id": resp.id, "link": str(resp.url), "date": date}
                )
                link_id = result.scalar()

                if resp.tags:
                    await session.execute(
                        text("INSERT INTO link_tag (link_id, tag) VALUES " +
                             ", ".join(f"(:link_id, :tag{i})" for i in range(len(resp.tags)))),
                        {"link_id": link_id, **{f"tag{i}": tag for i, tag in enumerate(resp.tags)}}
                    )

                if resp.filters:
                    await session.execute(
                        text("INSERT INTO link_filter (link_id, filter) VALUES " +
                             ", ".join(f"(:link_id, :filter{i})" for i in range(len(resp.filters)))),
                        {"link_id": link_id, **{f"filter{i}": f for i, f in enumerate(resp.filters)}}
                    )
        logger.info("add_end", extra={"tg_id": resp.id, "url": resp.url})

    async def delete(self, tg_chat_id: int, link: str) -> LinkResponse:

        """
        Удаляет ссылку для пользователя по его tg_chat_id и url ссылки.

        Параметры:
            tg_chat_id (int): Идентификатор чата в Telegram.
            link (str): URL ссылки, которую нужно удалить.

        Возвращает:
            LinkResponse: Ответ с информацией о удаленной ссылке.

        Исключения:
            ChatIsNotRegisteredException: Если пользователь не найден в базе данных.
            LinkIsNotFoundException: Если ссылка не найдена в базе данных.
        """

        logger.info("delete_start", extra={"tg_id": tg_chat_id, "link": link})
        async with session_factory() as session:
            async with session.begin():
                user = await session.execute(text("SELECT id FROM users WHERE id = :tg_chat_id"),
                                             {"tg_chat_id": tg_chat_id})
                if not user.scalar_one_or_none():
                    logger.error("chat_not_found", extra={"tg_id": tg_chat_id})
                    raise ChatIsNotRegisteredException(f"Чат {tg_chat_id} не зарегистрирован")

                result = await session.execute(text("""
                    SELECT ld.link_id, ld.tg_id, ld.link, 
                           COALESCE(array_agg(DISTINCT lf.filter) FILTER (WHERE lf.filter IS NOT NULL), '{}') AS filters, 
                           COALESCE(array_agg(DISTINCT lt.tag) FILTER (WHERE lt.tag IS NOT NULL), '{}') AS tags
                    FROM link_date ld
                    LEFT JOIN link_filter lf ON ld.link_id = lf.link_id
                    LEFT JOIN link_tag lt ON ld.link_id = lt.link_id
                    WHERE ld.tg_id = :tg_chat_id AND ld.link = :link
                    GROUP BY ld.link_id, ld.tg_id, ld.link
                """), {"tg_chat_id": tg_chat_id, "link": link})

                link_obj = result.fetchone()
                if not link_obj:
                    logger.error("link_not_found", extra={"tg_id": tg_chat_id, "link": link})
                    raise LinkIsNotFoundException(f"Ссылка {link} не отслеживается")

                await session.execute(text("""
                    DELETE FROM link_date WHERE tg_id = :tg_chat_id AND link = :link
                """), {"tg_chat_id": tg_chat_id, "link": link})

                logger.info("delete_end", extra={"tg_id": tg_chat_id, "link": link})

                return LinkResponse(
                    id=link_obj.link_id,
                    url=HttpUrl(link_obj.link),
                    filters=link_obj.filters if isinstance(link_obj.filters, list) else [],
                    tags=link_obj.tags if isinstance(link_obj.tags, list) else []
                )

    async def get_all(self, page: int, page_size: int = 50) -> List[LinkDTO]:

        """
        Получает все ссылки с пагинацией.

        Параметры:
            page (int): Номер страницы.
            page_size (int): Количество ссылок на странице.

        Возвращает:
            List[LinkDTO]: Список ссылок с их данными.
        """

        logger.info("get_all_start", extra={"page": page, "page_size": page_size})
        async with session_factory() as session:
            offset = (page - 1) * page_size
            result = await session.execute(
                text("""
                    SELECT ld.link_id, ld.tg_id, ld.link, ld.date,
                           COALESCE(array_agg(DISTINCT lf.filter) FILTER (WHERE lf.filter IS NOT NULL), '{}') AS filters,
                           COALESCE(array_agg(DISTINCT lt.tag) FILTER (WHERE lt.tag IS NOT NULL), '{}') AS tags
                    FROM link_date ld
                    LEFT JOIN link_filter lf ON ld.link_id = lf.link_id
                    LEFT JOIN link_tag lt ON ld.link_id = lt.link_id
                    GROUP BY ld.link_id, ld.tg_id, ld.link, ld.date
                    LIMIT :page_size OFFSET :offset
                """),
                {"page_size": page_size, "offset": offset}
            )

            links = result.mappings().all()
            logger.info("get_all_end", extra={"links_count": len(links)})
            return [
                LinkDTO(
                    link_id=row["link_id"],
                    tg_id=row["tg_id"],
                    link=row["link"],
                    date=row["date"],
                    filters=row["filters"],
                    tags=row["tags"]
                )
                for row in links
            ]

    async def delete_tag(self, tg_id: int, link: str, tag: str) -> None:

        """
        Удаляет тег из ссылки для указанного tg_id.

        Параметры:
            tg_id (int): Идентификатор чата в Telegram.
            link (str): URL ссылки, из которой нужно удалить тег.
            tag (str): Тег, который нужно удалить.

        Исключения:
            ChatIsNotRegisteredException: Если пользователь не найден в базе данных.
            LinkIsNotFoundException: Если ссылка не найдена в базе данных.
            LinkWithTagIsNotFound: Если указанная ссылка не имеет заданного тега.
        """

        logger.info("delete_tag_start", extra={"tg_id": tg_id, "link": link, "tag": tag})
        async with session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    text("SELECT id FROM users WHERE id = :tg_id"),
                    {"tg_id": tg_id}
                )
                user = result.scalar_one_or_none()
                if not user:
                    logger.error("chat_not_found", extra={"tg_id": tg_id})
                    raise ChatIsNotRegisteredException(f"Чат с {tg_id} не зарегистрирован")

                result = await session.execute(
                    text("SELECT link_id FROM link_date WHERE link = :link AND tg_id = :tg_id"),
                    {"link": link, "tg_id": tg_id}
                )
                link_id = result.scalar_one_or_none()
                if not link_id:
                    logger.error("link_not_found", extra={"tg_id": tg_id, "link": link})
                    raise LinkIsNotFoundException(f"Чат {tg_id} не отслеживает {link}")

                result = await session.execute(
                    text("SELECT link_id FROM link_tag WHERE link_id = :link_id AND tag = :tag"),
                    {"link_id": link_id, "tag": tag}
                )
                tag_obj = result.scalar_one_or_none()
                if not tag_obj:
                    logger.error("tag_not_found", extra={"tg_id": tg_id, "link": link, "tag": tag})
                    raise LinkWithTagIsNotFound(f"{tg_id} не имеет ссылки {link} с тегом {tag}")

                await session.execute(
                    text("DELETE FROM link_tag WHERE link_id = :link_id AND tag = :tag"),
                    {"link_id": link_id, "tag": tag}
                )
        logger.error("tag_not_found", extra={"tg_id": tg_id, "link": link, "tag": tag})

    async def add_tag(self, tg_id: int, link: str, tag: str) -> None:

        """
        Добавляет новый тег для указанной ссылки пользователя.

        Параметры:
            tg_id (int): Идентификатор чата в Telegram.
            link (str): URL ссылки, к которой нужно добавить тег.
            tag (str): Тег, который нужно добавить.

        Исключения:
            ChatIsNotRegisteredException: Если пользователь с tg_id не найден.
            LinkIsNotFoundException: Если указанная ссылка не отслеживается пользователем.
        """

        logger.info("add_tag_start", extra={"tg_id": tg_id, "link": link, "tag": tag})
        async with session_factory() as session:
            async with session.begin():
                user_result = await session.execute(
                    text("SELECT id FROM users WHERE id = :tg_id"), {"tg_id": tg_id}
                )
                user = user_result.scalar_one_or_none()
                if not user:
                    logger.error("chat_not_found", extra={"tg_id": tg_id})
                    raise ChatIsNotRegisteredException(f"Чат {tg_id} не зарегистрирован")

                link_result = await session.execute(
                    text("SELECT link_id FROM link_date WHERE link = :link AND tg_id = :tg_id"),
                    {"link": link, "tg_id": tg_id}
                )
                link_obj = link_result.scalar_one_or_none()
                if not link_obj:
                    logger.error("link_not_found", extra={"tg_id": tg_id, "link": link})
                    raise LinkIsNotFoundException(f"Чат {tg_id} не отслеживает ссылку {link}")

                tag_result = await session.execute(
                    text("SELECT 1 FROM link_tag WHERE link_id = :link_id AND tag = :tag"),
                    {"link_id": link_obj, "tag": tag}
                )
                if tag_result.scalar_one_or_none():
                    raise TagAlreadyExistsException(f"Чат {tg_id} уже отслеживает ссылку {link} с таким тегом {tag}")

                await session.execute(
                    text("INSERT INTO link_tag (link_id, tag) VALUES (:link_id, :tag)"),
                    {"link_id": link_obj, "tag": tag}
                )
        logger.info("add_tag_end", extra={"tg_id": tg_id, "link": link, "tag": tag})

    async def change_date(self, link_id: int, date: str) -> None:

        """
        Изменяет дату для указанной ссылки.

        Параметры:
            link_id (int): Идентификатор ссылки.
            date (str): Новая дата для ссылки.

        Исключения:
            LinkIsNotFoundException: Если ссылка с указанным link_id не найдена.
        """

        logger.info("change_date_start", extra={"link_id": link_id, "date": date})
        async with session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    text("UPDATE link_date SET date = :date WHERE link_id = :link_id RETURNING link_id"),
                    {"date": date, "link_id": link_id}
                )
                updated_row = result.scalar_one_or_none()

                if updated_row is None:
                    logger.error("link_not_found", extra={"link_id": link_id})
                    raise LinkIsNotFoundException(f"Ссылка с id {link_id} не отслеживается")
                logger.info("date_changed", extra={"link_id": link_id, "new_date": date})
        logger.info("change_date_end", extra={"link_id": link_id, "date": date})
