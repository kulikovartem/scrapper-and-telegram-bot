#  type: ignore

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from testcontainers.postgres import PostgresContainer
from src.scrapper.exceptions import TagAlreadyExistsException
from src.scrapper.db.models.user import User
from src.scrapper.db.models.link_date import LinkDate
from src.scrapper.repos.orm_link_repo import OrmLinkRepo   #  type: ignore
from src.scrapper.schemas.link_response import LinkResponse
from src.scrapper.exceptions import AlreadyRegisteredChatException
from src.scrapper.exceptions import ChatIsNotRegisteredException
from pydantic import HttpUrl
from src.scrapper.db.config import Base
from sqlalchemy import and_
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from src.scrapper.exceptions import LinkIsNotFoundException
from src.scrapper.exceptions import LinkWithTagIsNotFound
from src.scrapper.db.models.link_tag import LinkTag


@pytest_asyncio.fixture(scope="session")
async def postgres_db():    # type: ignore
    with PostgresContainer("postgres:14").with_env("POSTGRES_HOST_AUTH_METHOD", "trust").with_exposed_ports(6578) as postgres_container:
        DATABASE_URL = postgres_container.get_connection_url()
        DATABASE_URL = DATABASE_URL.replace("psycopg2", "psycopg")

        engine = create_async_engine(DATABASE_URL, echo=True)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield engine

        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(postgres_db) -> AsyncSession:    # type: ignore
    SessionFactory = async_sessionmaker(
        bind=postgres_db,
        class_=AsyncSession,
        expire_on_commit=False   # type: ignore
    )

    async with SessionFactory() as session:
        yield session


@pytest.fixture
def link_repo():    # type: ignore
    return OrmLinkRepo()


@pytest.mark.asyncio
async def test_register_new_user(postgres_db, link_repo: OrmLinkRepo, db_session):    # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 777

    stmt = select(User).where(User.id == tg_id)
    existing_user = await db_session.execute(stmt)
    assert existing_user.scalar_one_or_none() is None

    await link_repo.register(tg_id)

    user = await db_session.get(User, tg_id)
    assert user is not None
    assert user.id == tg_id


@pytest.mark.asyncio
async def test_register_existing_user(postgres_db, link_repo: OrmLinkRepo):    # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)
    tg_id = 777

    with pytest.raises(AlreadyRegisteredChatException):
        await link_repo.register(tg_id)


@pytest.mark.asyncio
async def test_delete_existing_user(postgres_db, link_repo: OrmLinkRepo, db_session):   # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)
    tg_id = 999

    await link_repo.register(tg_id)

    user = await db_session.get(User, tg_id)
    assert user is not None
    assert user.id == tg_id

    await link_repo.delete_by_tg_id(tg_id)

    stmt = select(User).where(User.id == tg_id)
    user = await db_session.execute(stmt)
    user = user.scalar()

    assert user is None


@pytest.mark.asyncio
async def test_delete_non_existing_user(postgres_db, link_repo: OrmLinkRepo, db_session):     # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)
    tg_id = 1234

    user = await db_session.get(User, tg_id)
    assert user is None

    with pytest.raises(ChatIsNotRegisteredException):
        await link_repo.delete_by_tg_id(tg_id)


@pytest.mark.asyncio
async def test_add_link(postgres_db, db_session, link_repo: OrmLinkRepo):     # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)
    tg_id = 1234
    url = "https://example.com"
    date = "2025-04-02"
    formatted_url = url + '/'

    await link_repo.register(tg_id)

    resp = LinkResponse(id=tg_id, url=HttpUrl(url), filters=[], tags=["tag1", "tag2"])

    await link_repo.add(resp, date)

    stmt = select(LinkDate).where(and_(LinkDate.tg_id == tg_id, LinkDate.link == formatted_url))
    result = await db_session.execute(stmt)
    link = result.scalar_one_or_none()

    assert link.link == formatted_url
    assert link.tg_id == tg_id


@pytest.mark.asyncio
async def test_list_links_empty(postgres_db, link_repo: OrmLinkRepo):     # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 111
    await link_repo.register(tg_id)

    response = await link_repo.list(tg_id, page=1, page_size=10)

    assert response.size == 0
    assert response.links == []


@pytest.mark.asyncio
async def test_list_links_with_data(postgres_db, link_repo: OrmLinkRepo):    # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 222
    await link_repo.register(tg_id)

    url1 = "https://example.com/1"
    url2 = "https://example.com/2"

    await link_repo.add(LinkResponse(id=tg_id, url=HttpUrl(url1), filters=[], tags=[]), "2025-04-02")
    await link_repo.add(LinkResponse(id=tg_id, url=HttpUrl(url2), filters=[], tags=[]), "2025-04-02")

    response = await link_repo.list(tg_id, page=1, page_size=10)

    assert response.size == 2
    assert {str(link.url) for link in response.links} == {url1, url2}


@pytest.mark.asyncio
async def test_list_links_pagination(postgres_db, link_repo: OrmLinkRepo):     # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 333
    await link_repo.register(tg_id)

    urls = [f"https://example.com/{i}" for i in range(1, 6)]

    for url in urls:
        await link_repo.add(LinkResponse(id=tg_id, url=HttpUrl(url), filters=[], tags=[]), "2025-04-02")

    response_page_1 = await link_repo.list(tg_id, page=1, page_size=2)
    response_page_2 = await link_repo.list(tg_id, page=2, page_size=2)

    assert response_page_1.size == 2
    assert response_page_2.size == 2

    page_1_urls = {link.url for link in response_page_1.links}
    page_2_urls = {link.url for link in response_page_2.links}

    assert page_1_urls != page_2_urls


@pytest.mark.asyncio
async def test_list_links_not_registered(postgres_db, link_repo: OrmLinkRepo):    # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 444

    with pytest.raises(ChatIsNotRegisteredException):
        await link_repo.list(tg_id, page=1, page_size=10)


@pytest.mark.asyncio
async def test_delete_existing_link(postgres_db, link_repo: OrmLinkRepo, db_session):    # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 555
    link_url = "https://example.com/delete-me"

    await link_repo.register(tg_id)
    await link_repo.add(LinkResponse(id=tg_id, url=HttpUrl(link_url), filters=[], tags=[]), "2025-04-02")

    link_in_db = await db_session.execute(select(LinkDate).where(LinkDate.link == link_url))
    assert link_in_db.scalar_one_or_none() is not None

    deleted_link = await link_repo.delete(tg_id, link_url)

    assert str(deleted_link.url) == link_url

    link_in_db = await db_session.execute(select(LinkDate).where(LinkDate.link == link_url))
    assert link_in_db.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_link_chat_not_registered(postgres_db, link_repo: OrmLinkRepo, db_session):    # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 666
    link_url = "https://example.com/nonexistent"

    with pytest.raises(ChatIsNotRegisteredException):
        await link_repo.delete(tg_id, link_url)


@pytest.mark.asyncio
async def test_delete_link_not_found(postgres_db, link_repo: OrmLinkRepo):    # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 888
    link_url = "https://example.com/missing"

    await link_repo.register(tg_id)

    with pytest.raises(LinkIsNotFoundException):
        await link_repo.delete(tg_id, link_url)


@pytest.mark.asyncio
async def test_delete_existing_tag(postgres_db, link_repo: OrmLinkRepo, db_session):    # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 123
    link = "https://example.com"
    tag = "news"

    await link_repo.register(tg_id)

    await link_repo.add(LinkResponse(id=tg_id, url=HttpUrl(link), filters=[], tags=[tag]), "2025-04-02")

    formatted_link = link + '/'
    link_obj = (await db_session.execute(
        select(LinkDate).where(LinkDate.link == formatted_link, LinkDate.tg_id == tg_id))).scalar_one_or_none()
    assert link_obj is not None

    link_id = link_obj.link_id

    tag_obj = (await db_session.execute(
        select(LinkTag).where(LinkTag.link_id == link_id, LinkTag.tag == tag))).scalar_one_or_none()
    assert tag_obj is not None, "Тег не был добавлен в базу"

    await link_repo.delete_tag(tg_id, formatted_link, tag)

    tag_obj = (await db_session.execute(
        select(LinkTag).where(LinkTag.link_id == link_id, LinkTag.tag == tag))).scalar_one_or_none()
    assert tag_obj is None, "Тег не был удалён"


@pytest.mark.asyncio
async def test_delete_tag_from_unregistered_chat(link_repo: OrmLinkRepo):   # type: ignore
    tg_id = 654
    link = "https://example.com"
    tag = "news"

    with pytest.raises(ChatIsNotRegisteredException):
        await link_repo.delete_tag(tg_id, link, tag)


@pytest.mark.asyncio
async def test_delete_tag_from_nonexistent_link(postgres_db, link_repo: OrmLinkRepo):   # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 345
    link = "https://nonexistent.com"
    tag = "news"

    await link_repo.register(tg_id)

    with pytest.raises(LinkIsNotFoundException):
        await link_repo.delete_tag(tg_id, link, tag)


@pytest.mark.asyncio
async def test_delete_nonexistent_tag(postgres_db, link_repo: OrmLinkRepo):    # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 789
    link = "https://example.com"
    formatted_link = link + '/'

    await link_repo.register(tg_id)

    await link_repo.add(LinkResponse(id=tg_id, url=HttpUrl(link), filters=[], tags=[]), "2025-04-02")

    with pytest.raises(LinkWithTagIsNotFound):
        await link_repo.delete_tag(tg_id, formatted_link, "nonexistent")


@pytest.mark.asyncio
async def test_add_tag(postgres_db, link_repo: OrmLinkRepo, db_session):    # type: ignore
    from src.scrapper.db.config import session_factory
    session_factory.configure(bind=postgres_db)

    tg_id = 100000
    link = "https://example.com"
    tag = "news"

    with pytest.raises(ChatIsNotRegisteredException):
        await link_repo.add_tag(tg_id, link, tag)

    await link_repo.register(tg_id)

    with pytest.raises(LinkIsNotFoundException):
        await link_repo.add_tag(tg_id, link, tag)

    await link_repo.add(LinkResponse(id=tg_id, url=HttpUrl(link), filters=[], tags=[]), "2025-04-02")

    formatted_link = link + '/'

    await link_repo.add_tag(tg_id, formatted_link, tag)

    link_obj = (await db_session.execute(select(LinkDate).where(LinkDate.link == formatted_link, LinkDate.tg_id == tg_id))).scalar_one_or_none()
    assert link_obj is not None, "Ссылка не была добавлена в базу"

    tag_obj = (await db_session.execute(select(LinkTag).where(LinkTag.link_id == link_obj.link_id, LinkTag.tag == tag))).scalar_one_or_none()
    assert tag_obj is not None, "Тег не был добавлен в базу"

    with pytest.raises(TagAlreadyExistsException):
        await link_repo.add_tag(tg_id, formatted_link, tag)

