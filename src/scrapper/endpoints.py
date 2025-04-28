from fastapi import APIRouter, Path, Header, Body, status
import logging
from pydantic import HttpUrl
from typing import List
from src.scrapper.exceptions.already_registered_exception import AlreadyRegisteredChatException
from src.scrapper.exceptions.chat_is_not_registered_exception import ChatIsNotRegisteredException
from src.scrapper.exceptions.not_successful_response_exception import NotSuccessfulResponseException
from src.scrapper.exceptions.not_supported_type_of_filter_exception import NotSupportedTypeOfFilter
from src.scrapper.schemas.remove_link_request import RemoveLinkRequest
from src.scrapper.schemas.add_link_request import AddLinkRequest
from src.scrapper.schemas.link_response import LinkResponse
from src.scrapper.schemas.api_error_response import ApiErrorResponse
from src.scrapper.schemas.list_links_response import ListLinksResponse
from src.scrapper.exceptions.api_error_exception import ApiErrorException
from src.scrapper.repo_factory import RepoFactory
from src.scrapper.client_factory import ClientFactory
from src.scrapper.exceptions.url_is_not_supported_exception import UrlIsNotSupportedException
from src.scrapper.exceptions.resource_is_not_found_exception import ResourceIsNotFoundException
from src.scrapper.exceptions.link_is_not_found_exception import LinkIsNotFoundException
from src.scrapper.exceptions.url_is_already_followed_exception import UrlIsAlreadyFollowed
from src.scrapper.url_type_definer import URLTypeDefiner
from src.scrapper.db.db_settings import DBSettings
from src.scrapper.schemas.remove_tag_request import RemoveTagRequest
from src.scrapper.exceptions.link_with_tag_is_not_found import LinkWithTagIsNotFound
from src.scrapper.schemas.add_tag_request import AddTagRequest
from src.scrapper.exceptions.tag_already_exists_exception import TagAlreadyExistsException

logger = logging.getLogger(__name__)

scrapper_router = APIRouter()

db_settings = DBSettings()

REPO = RepoFactory.create(db_settings.DB_SERVICE_TYPE)


@scrapper_router.post("/tg-chat/{id}", status_code=status.HTTP_200_OK, description="Чат зарегистрирован")
async def create_chat(id: int = Path(...)) -> None:
    """
    Регистрирует Telegram-чат для отслеживания ссылок.

    Принимает идентификатор чата в пути и регистрирует его в репозитории ссылок.
    Если чат уже зарегистрирован, возвращает ошибку с кодом 409.

    Args:
        id (int): Идентификатор Telegram-чата, передаваемый как параметр пути.

    Raises:
        ApiErrorException: Если чат уже зарегистрирован.
    """
    try:
        logger.info("Регистрация чата", extra={"chat_id": id})
        await REPO.register(tg_id=id)
    except AlreadyRegisteredChatException as e:
        logger.error("Ошибка регистрации: чат уже зарегистрирован", extra={"chat_id": id, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Чат уже зарегистрирован",
            code="AlreadyRegisteredChatException",
            exceptionName="AlreadyRegisteredChatException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 55, in create_chat"]
        )
        raise ApiErrorException(error_data, status.HTTP_409_CONFLICT)


@scrapper_router.delete("/tg-chat/{id}", status_code=status.HTTP_200_OK, description="Чат успешно удалён")
async def delete_chat(id: int = Path(...)) -> None:
    """
    Удаляет Telegram-чат из репозитория ссылок.

    Принимает идентификатор чата в пути и удаляет все данные, связанные с этим чатом.
    Если чат не зарегистрирован, возвращает ошибку с кодом 404.

    Args:
        id (int): Идентификатор Telegram-чата, передаваемый как параметр пути.

    Raises:
        ApiErrorException: Если чат не найден.
    """
    try:
        logger.info("Удаление чата", extra={"chat_id": id})
        await REPO.delete_by_tg_id(tg_id=id)
    except ChatIsNotRegisteredException as e:
        logger.error("Ошибка удаления: чат не найден", extra={"chat_id": id, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Чат не найден",
            code="ChatIsNotRegisteredException",
            exceptionName="ChatIsNotRegisteredException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 84, in delete_chat"]
        )
        raise ApiErrorException(error_data, status.HTTP_404_NOT_FOUND)


@scrapper_router.get("/links", response_model=ListLinksResponse, status_code=status.HTTP_200_OK, description="Ссылки успешно получены")
async def get_links(tg_chat_id: int = Header(...)) -> ListLinksResponse:
    """
    Возвращает список ссылок, отслеживаемых указанным Telegram-чатом.

    Чат идентифицируется через заголовок запроса. Если чат не зарегистрирован,
    возвращается ошибка с кодом 404.

    Args:
        tg_chat_id (int): Идентификатор Telegram-чата, передаваемый в заголовке запроса.

    Returns:
        ListLinksResponse: Объект, содержащий список ссылок и их количество.

    Raises:
        ApiErrorException: Если чат не зарегистрирован.
    """
    try:
        logger.info("Получение ссылок", extra={"tg_chat_id": tg_chat_id})
        lst: List[LinkResponse] = []
        page = 1
        while True:
            result = await REPO.list(tg_id=tg_chat_id, page=page, page_size=db_settings.DB_PAGESIZE)
            if not result.links:
                return ListLinksResponse(links=lst, size=len(lst))
            else:
                lst.extend(result.links)
            page += 1
    except ChatIsNotRegisteredException as e:
        logger.error("Ошибка получения ссылок: чат не зарегистрирован", extra={"tg_chat_id": tg_chat_id, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Чат не зарегистрирован",
            code="ChatIsNotRegisteredException",
            exceptionName="ChatIsNotRegisteredException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 116, in get_links"]
        )
        raise ApiErrorException(error_data, status.HTTP_404_NOT_FOUND)


@scrapper_router.post("/links", response_model=LinkResponse, status_code=status.HTTP_200_OK, description="Ссылка успешно добавлена")
async def create_link(tg_chat_id: int = Header(...), request: AddLinkRequest = Body(...)) -> LinkResponse:
    """
    Добавляет новую ссылку для отслеживания в репозиторий.

    Чат идентифицируется через заголовок запроса. На основании URL определяется, к какому сервису относится ссылка
    (GitHub или StackOverflow), затем запрашивается дата обновления ссылки через соответствующий клиент.
    Если URL или фильтры некорректны, или ресурс не найден, возвращается ошибка с соответствующим HTTP-кодом.
    Если чат не зарегистрирован или URL уже отслеживается, также возвращается ошибка.

    Args:
        tg_chat_id (int): Идентификатор Telegram-чата, передаваемый в заголовке запроса.
        request (AddLinkRequest): Объект запроса, содержащий URL, фильтры и тэги ссылки.

    Returns:
        LinkResponse: Объект, представляющий добавленную ссылку.

    Raises:
        ApiErrorException: При ошибках валидации URL, фильтров, отсутствия ресурса,
                           неуспешного ответа API, не зарегистрированного чата или дублирования URL.
    """
    logger.info("Добавление ссылки", extra={"tg_chat_id": tg_chat_id, "link": str(request.link)})
    link_str = str(request.link)
    try:
        url_type = URLTypeDefiner.define(url=link_str)
        client = ClientFactory.create_client(url_type)
    except UrlIsNotSupportedException:
        logger.error("Неизвестный тип ссылки", extra={"link": link_str})
        error_data = ApiErrorResponse(
            description="Неизвестный тип ссылки",
            code="UndefinedURLType",
            exceptionName="UndefinedURLType",
            exceptionMessage="Тип ссылки не поддерживается",
            stacktrace=["File 'endpoints.py', line 154, in create_link"]
        )
        raise ApiErrorException(error_data, status.HTTP_400_BAD_REQUEST)
    try:
        info = await client.get_info_by_url_with_filters(link_str, request.filters)
        date = info["date"]
    except UrlIsNotSupportedException as e:
        logger.error("Некорректная ссылка", extra={"link": link_str, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Некорректная ссылка",
            code="UrlIsNotSupportedException",
            exceptionName="UrlIsNotSupportedException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 166, in create_link"]
        )
        raise ApiErrorException(error_data, status.HTTP_400_BAD_REQUEST)
    except NotSupportedTypeOfFilter as e:
        logger.error("Неподдерживаемый тип фильтра", extra={"filters": request.filters, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Неподдерживаемый тип фильтра",
            code="NotSupportedTypeOfFilter",
            exceptionName="NotSupportedTypeOfFilter",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 176, in create_link"]
        )
        raise ApiErrorException(error_data, status.HTTP_400_BAD_REQUEST)
    except ResourceIsNotFoundException as e:
        logger.error("Ресурс не найден", extra={"link": link_str, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Ресурс не найден",
            code="ResourceIsNotFoundException",
            exceptionName="ResourceIsNotFoundException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 186, in create_link"]
        )
        raise ApiErrorException(error_data, status.HTTP_400_BAD_REQUEST)
    except NotSuccessfulResponseException as e:
        logger.error("Ошибка запроса к API", extra={"link": link_str, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Ошибка запроса к API",
            code="NotSuccessfulResponseException",
            exceptionName="NotSuccessfulResponseException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 196, in create_link"]
        )
        raise ApiErrorException(error_data, status.HTTP_400_BAD_REQUEST)
    try:
        resp = LinkResponse(
            id=tg_chat_id,
            url=HttpUrl(link_str),
            tags=request.tags,
            filters=request.filters
        )
        await REPO.add(resp, date)
        logger.info("Ссылка успешно добавлена", extra={"tg_chat_id": tg_chat_id, "link": link_str})
        return resp
    except ChatIsNotRegisteredException as e:
        logger.error("Чат не зарегистрирован при добавлении ссылки", extra={"tg_chat_id": tg_chat_id, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Чат не зарегистрирован",
            code="ChatIsNotRegisteredException",
            exceptionName="ChatIsNotRegisteredException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 216, in create_link"]
        )
        raise ApiErrorException(error_data, status.HTTP_404_NOT_FOUND)
    except UrlIsAlreadyFollowed as e:
        logger.error("URL уже отслеживается", extra={"tg_chat_id": tg_chat_id, "link": link_str, "error": str(e)})
        error_data = ApiErrorResponse(
            description="URL уже отслеживается",
            code="UrlIsAlreadyFollowed",
            exceptionName="UrlIsAlreadyFollowed",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 226, in create_link"]
        )
        raise ApiErrorException(error_data, status.HTTP_409_CONFLICT)


@scrapper_router.delete("/links", response_model=LinkResponse, status_code=status.HTTP_200_OK, description="Ссылка успешно убрана")
async def delete_link(tg_chat_id: int = Header(...), request: RemoveLinkRequest = Body(...)) -> LinkResponse:
    """
    Удаляет указанную ссылку из репозитория для заданного Telegram-чата.

    Чат идентифицируется через заголовок запроса, а URL ссылки — через тело запроса.
    Если ссылка удалена успешно, возвращается объект LinkResponse, представляющий удалённую ссылку.
    В случае отсутствия ссылки или несуществующего чата возвращается соответствующая ошибка.

    Args:
        tg_chat_id (int): Идентификатор Telegram-чата, передаваемый в заголовке запроса.
        request (RemoveLinkRequest): Объект запроса, содержащий URL ссылки, которую необходимо удалить.

    Returns:
        LinkResponse: Объект, представляющий удалённую ссылку.

    Raises:
        ApiErrorException: Если ссылка не найдена или чат не зарегистрирован.
    """
    try:
        logger.info("Удаление ссылки", extra={"tg_chat_id": tg_chat_id, "link": str(request.link)})
        link_str = str(request.link)
        result = await REPO.delete(tg_chat_id=tg_chat_id, link=link_str)
        logger.info("Ссылка удалена успешно", extra={"tg_chat_id": tg_chat_id, "link": link_str})
        return result
    except LinkIsNotFoundException as e:
        logger.error("Ссылка не найдена", extra={"tg_chat_id": tg_chat_id, "link": str(request.link), "error": str(e)})
        error_data = ApiErrorResponse(
            description="Ссылка не найдена",
            code="LinkIsNotFoundException",
            exceptionName="LinkIsNotFoundException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 263, in delete_link"]
        )
        raise ApiErrorException(error_data, status.HTTP_404_NOT_FOUND)
    except ChatIsNotRegisteredException as e:
        logger.error("Чат не найден", extra={"tg_chat_id": tg_chat_id, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Чат не найден",
            code="ChatNotFoundException",
            exceptionName="ChatNotFoundException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 273, in delete_link"]
        )
        raise ApiErrorException(error_data, status.HTTP_404_NOT_FOUND)


@scrapper_router.delete("/tags", status_code=status.HTTP_200_OK)
async def delete_tag(tg_chat_id: int = Header(...), request: RemoveTagRequest = Body(...)) -> None:
    """
    Удаляет тег с указанной ссылки.

    Параметры:
        tg_chat_id (int): Идентификатор чата Telegram, из которого будет удален тег.
        request (RemoveTagRequest): Тело запроса, содержащее URL ссылки и тег, который необходимо удалить.

    Исключения:
        ChatIsNotRegisteredException: Если чат с указанным tg_chat_id не найден.
        LinkIsNotFoundException: Если указанная ссылка не найдена.
        LinkWithTagIsNotFound: Если тег не найден на указанной ссылке.

    Возвращает:
        str: Сообщение об успешном удалении тега или ошибке, если таковая возникла.
    """
    try:
        await REPO.delete_tag(tg_id=tg_chat_id, link=str(request.url), tag=request.tag)
    except ChatIsNotRegisteredException as e:
        logger.error("Чат не зарегистрирован", extra={"tg_chat_id": tg_chat_id, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Чат не зарегистрирован",
            code="ChatNotFoundException",
            exceptionName="ChatNotFoundException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 301, in delete_tag"]
        )
        raise ApiErrorException(error_data, status.HTTP_404_NOT_FOUND)
    except LinkIsNotFoundException as e:
        logger.error("Ссылка не найдена", extra={"tg_chat_id": tg_chat_id, "link": str(request.url), "error": str(e)})
        error_data = ApiErrorResponse(
            description="Ссылка не найдена",
            code="LinkIsNotFoundException",
            exceptionName="LinkIsNotFoundException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 309, in delete_tag"]
        )
        raise ApiErrorException(error_data, status.HTTP_404_NOT_FOUND)
    except LinkWithTagIsNotFound as e:
        logger.error("Ссылка c тегом не найдена", extra={"tg_chat_id": tg_chat_id, "link": str(request.url),
                                                         "tag": request.tag, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Ссылка c данным тегом не найдена",
            code="LinkWithTagIsNotFound",
            exceptionName="LinkWithTagIsNotFound",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 321, in delete_tag"]
        )
        raise ApiErrorException(error_data, status.HTTP_404_NOT_FOUND)


@scrapper_router.post("/tags", status_code=status.HTTP_200_OK)
async def create_tag(tg_chat_id: int = Header(...), request: AddTagRequest = Body(...)) -> None:
    """
    Добавляет новый тег к указанной ссылке.

    Параметры:
        tg_chat_id (int): Идентификатор чата Telegram, в котором будет добавлен тег.
        request (AddTagRequest): Тело запроса, содержащее URL ссылки и тег, который нужно добавить.

    Исключения:
        ChatIsNotRegisteredException: Если чат с указанным tg_chat_id не найден.
        LinkIsNotFoundException: Если указанная ссылка не найдена.
        TagAlreadyExistsException: Если тег уже существует для указанной ссылки.

    Возвращает:
        str: Сообщение об успешном добавлении тега или ошибке, если таковая возникла.
    """
    try:
        await REPO.add_tag(tg_id=tg_chat_id, link=str(request.url), tag=request.tag)
    except ChatIsNotRegisteredException as e:
        logger.error("Чат не зарегистрирован", extra={"tg_chat_id": tg_chat_id, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Чат не зарегистрирован",
            code="ChatNotFoundException",
            exceptionName="ChatNotFoundException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 340, in create_tag"]
        )
        raise ApiErrorException(error_data, status.HTTP_404_NOT_FOUND)
    except LinkIsNotFoundException as e:
        logger.error("Ссылка не найдена", extra={"tg_chat_id": tg_chat_id, "link": str(request.url), "error": str(e)})
        error_data = ApiErrorResponse(
            description="Ссылка не найдена",
            code="LinkIsNotFoundException",
            exceptionName="LinkIsNotFoundException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 350, in delete_tag"]
        )
        raise ApiErrorException(error_data, status.HTTP_404_NOT_FOUND)
    except TagAlreadyExistsException as e:
        logger.error("Тег уже существует",
                     extra={"tg_chat_id": tg_chat_id, "link": str(request.url), "tag": request.tag, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Тег уже существует",
            code="TagAlreadyExistsException",
            exceptionName="TagAlreadyExistsException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 360, in create_tag"]
        )
        raise ApiErrorException(error_data, status.HTTP_409_CONFLICT)
