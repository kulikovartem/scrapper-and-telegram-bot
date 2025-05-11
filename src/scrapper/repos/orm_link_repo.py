from src.scrapper.schemas.link_response import LinkResponse
from src.scrapper.schemas.list_links_response import ListLinksResponse
from src.scrapper.db.models.link_date import LinkDate
from pydantic import HttpUrl
from src.scrapper.db.models.user import User
from src.scrapper.db.config import session_factory
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List
from src.scrapper.exceptions import UrlIsAlreadyFollowed
from src.scrapper.exceptions import LinkIsNotFoundException
from src.scrapper.exceptions import AlreadyRegisteredChatException
from src.scrapper.exceptions import ChatIsNotRegisteredException
from src.scrapper.schemas.link_dto import LinkDTO
from src.scrapper.interfaces.link_repo_interface import LinkRepo
from src.scrapper.exceptions import LinkWithTagIsNotFound
from src.scrapper.db.models.link_tag import LinkTag
from src.scrapper.db.models.link_filter import LinkFilter
from src.scrapper.exceptions import TagAlreadyExistsException
from src.scrapper.exceptions import UnsupportedTimeFormatException
from datetime import datetime, time
import logging

logger = logging.getLogger(__name__)


class OrmLinkRepo(LinkRepo):
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
        logger.info("register_start", extra={"tg_id": tg_id})
        async with session_factory() as session:
            async with session.begin():
                user = await session.get(User, tg_id)
                if not user:
                    new_user = User(id=tg_id)
                    session.add(new_user)
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
        logger.info("delete_start", extra={"tg_id": tg_id})
        async with session_factory() as session:
            async with session.begin():
                user = await session.get(User, tg_id)
                if user:
                    await session.delete(user)
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
            stmt = select(User.id).where(User.id == tg_id)
            user_exists = await session.execute(stmt)
            if not user_exists.scalar_one_or_none():
                logger.error("chat_not_found", extra={"tg_id": tg_id})
                raise ChatIsNotRegisteredException(f"Чат {tg_id} не зарегистрирован")

            stmt = (
                select(LinkDate)  # type: ignore
                .where(LinkDate.tg_id == tg_id)
                .options(
                    selectinload(LinkDate.filters),
                    selectinload(LinkDate.tags),
                )
                .limit(page_size)
                .offset((page - 1) * page_size)
            )

            result = await session.execute(stmt)
            links: list[LinkDate] = result.scalars().all()  # type: ignore

            logger.info("list_end", extra={"tg_id": tg_id, "links_count": len(links)})
            return ListLinksResponse(
                links=[
                    LinkResponse(
                        id=link.link_id,
                        url=HttpUrl(link.link),
                        filters=[f.filter for f in link.filters],
                        tags=[t.tag for t in link.tags],
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
                user = await session.get(User, resp.id)
                if not user:
                    logger.error("chat_not_found", extra={"tg_id": resp.id})
                    raise ChatIsNotRegisteredException(f"Чат {resp.id} не зарегистрирован")

                stmt = select(LinkDate).where(and_(LinkDate.tg_id == resp.id, LinkDate.link == str(resp.url)))
                link = await session.execute(stmt)
                if link.scalar():
                    logger.error("url_already_followed", extra={"tg_id": resp.id, "url": resp.url})
                    raise UrlIsAlreadyFollowed(f"Ссылка {resp.url} уже отслеживается")

                new_link = LinkDate(tg_id=resp.id, link=str(resp.url), date=date)
                session.add(new_link)

                await session.flush()

                session.add_all([LinkTag(link_id=new_link.link_id, tag=tag) for tag in resp.tags])
                session.add_all([LinkFilter(link_id=new_link.link_id, filter=f) for f in resp.filters])

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
                stmt = select(User).where(User.id == tg_chat_id)
                user = (await session.execute(stmt)).scalar_one_or_none()
                if not user:
                    logger.error("chat_not_found", extra={"tg_id": tg_chat_id})
                    raise ChatIsNotRegisteredException(f"Чат {tg_chat_id} не зарегистрирован")

                stmt = (
                    select(LinkDate)  # type: ignore
                    .where(and_(LinkDate.tg_id == tg_chat_id, LinkDate.link == link))
                    .options(selectinload(LinkDate.filters), selectinload(LinkDate.tags))
                )
                link_obj: LinkDate | None = (await session.execute(stmt)).scalar_one_or_none()   # type: ignore

                if not link_obj:
                    logger.error("link_not_found", extra={"tg_id": tg_chat_id, "link": link})
                    raise LinkIsNotFoundException(f"Ссылка {link} не отслеживается")

                resp = LinkResponse(
                    id=tg_chat_id,
                    url=HttpUrl(link_obj.link),
                    filters=[f.filter for f in link_obj.filters],
                    tags=[t.tag for t in link_obj.tags],
                )

                await session.delete(link_obj)

        logger.info("delete_end", extra={"tg_id": tg_chat_id, "link": link})
        return resp

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
            stmt = (
                select(LinkDate)
                .options(
                    selectinload(LinkDate.filters),
                    selectinload(LinkDate.tags)
                )
                .limit(page_size)
                .offset((page - 1) * page_size)
            )
            result = await session.execute(stmt)
            links = result.scalars().all()

            logger.info("get_all_end", extra={"links_count": len(links)})
            return [
                LinkDTO(
                    link_id=link.link_id,
                    tg_id=link.tg_id,
                    link=link.link,
                    date=link.date,
                    filters=[f.filter for f in link.filters],
                    tags=[t.tag for t in link.tags]
                )
                for link in links
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
                stmt = select(User).where(User.id == tg_id)
                user = (await session.execute(stmt)).scalar_one_or_none()
                if not user:
                    logger.error("chat_not_found", extra={"tg_id": tg_id})
                    raise ChatIsNotRegisteredException(f"Чат с {tg_id} не зарегистрирован")

                stmt = select(LinkDate.link_id).where(  # type: ignore
                    and_(LinkDate.link == link, LinkDate.tg_id == tg_id)
                )
                link_id = (await session.execute(stmt)).scalar_one_or_none()

                if not link_id:
                    logger.error("link_not_found", extra={"tg_id": tg_id, "link": link})
                    raise LinkIsNotFoundException(f"Чат {tg_id} не отслеживает {link}")

                stmt = select(LinkTag).where(   # type: ignore
                    and_(LinkTag.link_id == link_id, LinkTag.tag == tag)
                )
                tag_obj = (await session.execute(stmt)).scalar_one_or_none()

                if not tag_obj:
                    logger.error("tag_not_found", extra={"tg_id": tg_id, "link": link, "tag": tag})
                    raise LinkWithTagIsNotFound(f"{tg_id} не имеет ссылки {link} с тегом {tag}")

                await session.delete(tag_obj)
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
                stmt = select(User).where(User.id == tg_id)
                user = (await session.execute(stmt)).scalar_one_or_none()
                if not user:
                    logger.error("chat_not_found", extra={"tg_id": tg_id})
                    raise ChatIsNotRegisteredException(f"Чат с {tg_id} не зарегистрирован")

                stmt = select(LinkDate.link_id).where(    # type: ignore
                    and_(LinkDate.link == link, LinkDate.tg_id == tg_id)
                )
                link_id = (await session.execute(stmt)).scalar_one_or_none()

                if not link_id:
                    logger.error("link_not_found", extra={"tg_id": tg_id, "link": link})
                    raise LinkIsNotFoundException(f"Чат {tg_id} не отслеживает {link}")

                stmt = select(LinkTag).where(LinkTag.link_id == link_id, LinkTag.tag == tag)   # type: ignore
                existing_tag = await session.execute(stmt)
                existing_tag = existing_tag.scalar_one_or_none()    # type: ignore

                if existing_tag:
                    logger.error("tag_already_exists", extra={"tg_id": tg_id, "link": link, "tag": tag})
                    raise TagAlreadyExistsException(f"Ссылка {link_id} уже имеет тег {tag}")

                new_tag = LinkTag(link_id=link_id, tag=tag)
                session.add(new_tag)

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
                stmt = select(LinkDate).where(LinkDate.link_id == link_id)
                link = await session.execute(stmt)
                link: LinkDate | None = link.scalar_one_or_none()   # type: ignore
                if link:
                    link.date = date  # type: ignore
                    logger.info("date_changed", extra={"link_id": link_id, "new_date": date})
                else:
                    logger.error("link_not_found", extra={"link_id": link_id})
                    raise LinkIsNotFoundException(f"Ссылка с id {link_id} не отслеживается")
        logger.info("change_date_end", extra={"link_id": link_id, "date": date})

    async def change_time_push_up(self, tg_id: int, time_str: str | None) -> None:
        """
        Обновляет время push‑уведомлений (**time_push_up**) для указанного чата.

        Параметры:
            tg_id (int): Идентификатор чата Telegram.
            time_str (str | None): Время в формате «HH:MM» (24‑часовой)
                                   или `None`, чтобы сбросить значение.

        Исключения:
            UnsupportedTimeFormatException: Если `time_str` не «HH:MM» или выходит за диапазон.
            ChatIsNotRegisteredException:   Если чат с заданным `tg_id` не найден.
        """
        logger.info(
            "change_time_push_up_start",
            extra={"tg_id": tg_id, "time": time_str},
        )

        try:
            parsed = None if time_str is None else datetime.strptime(time_str, "%H:%M").time()
        except ValueError as exc:
            logger.error(
                "unsupported_time_format",
                extra={"tg_id": tg_id, "time": time_str, "error": str(exc)},
            )
            raise UnsupportedTimeFormatException(
                f"Подан неверный формат времени '{time_str}', ожидаю HH:MM"
            ) from exc

        async with session_factory() as session:
            async with session.begin():
                user = (
                    await session.execute(select(User).where(User.id == tg_id))
                ).scalar_one_or_none()

                if user is None:
                    logger.error("chat_not_found", extra={"tg_id": tg_id})
                    raise ChatIsNotRegisteredException(
                        f"Пользователь {tg_id} не зарегистрирован"
                    )

                user.time_push_up = parsed

        logger.info(
            "change_time_push_up_end",
            extra={
                "tg_id": tg_id,
                "new_time": parsed.isoformat(timespec="minutes") if parsed else None,
            },
        )

    async def get_time_push_up(self, tg_id: int) -> time | None:
        """
        Возвращает текущее время push‑уведомлений для чата.

        Параметры:
            tg_id (int): Идентификатор чата Telegram.

        Возвращает:
            Optional[time]: Объект `datetime.time`, если время задано, либо `None`.

        Исключения:
            ChatIsNotRegisteredException: Если чат с `tg_id` не зарегистрирован.
        """
        logger.info("get_time_push_up_start", extra={"tg_id": tg_id})

        async with session_factory() as session:
            stmt = select(User.time_push_up).where(User.id == tg_id)
            time_value: time | None = (await session.execute(stmt)).scalar_one_or_none()

            if time_value is None and not await session.get(User, tg_id):
                logger.error("chat_not_found", extra={"tg_id": tg_id})
                raise ChatIsNotRegisteredException(f"Пользователь {tg_id} не зарегистрирован")

        logger.info(
            "get_time_push_up_end",
            extra={
                "tg_id": tg_id,
                "time": time_value.isoformat(timespec='minutes') if time_value else None,
            },
        )
        return time_value
