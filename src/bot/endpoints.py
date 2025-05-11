import logging
from fastapi import APIRouter, Body, status
from telethon import TelegramClient
from src.tg_settings import TGBotSettings
from src.bot.schemas.api_error_response import ApiErrorResponse
from src.bot.exceptions.api_error_exception import ApiErrorException
from src.bot.schemas.link_update import LinkUpdate
from telethon.errors import RPCError, FloodWaitError, ChatWriteForbiddenError, MessageTooLongError

logger = logging.getLogger(__name__)

bot_router = APIRouter()

settings = TGBotSettings()  # type:ignore
client = TelegramClient("bot_api_session", settings.api_id, settings.api_hash)



@bot_router.post("/updates", status_code=status.HTTP_200_OK, description="Обновление обработано")
async def create(request: LinkUpdate = Body(...)) -> None:
    """
    Обрабатывает входящие запросы на обновление ссылок.

    Принимает объект запроса типа LinkUpdate, содержащий данные об обновлении ссылки,
    логирует полученный запрос и пытается отправить сообщение через Telethon клиент.

    Если сообщение отправлено успешно, логируется успешная отправка. В случае возникновения
    ошибки при отправке сообщения, формируется ответ об ошибке с описанием проблемы и выбрасывается
    ApiErrorException с кодом ошибки HTTP 400.

    Args:
        request (LinkUpdate): Объект, содержащий идентификатор получателя и URL обновленной ссылки.

    Raises:
        ApiErrorException: Если при отправке сообщения возникает исключительная ситуация.

    Returns:
        None
    """
    logger.info("Получен запрос обновления", extra={"request": request.dict()})
    try:
        await client.send_message(request.id, f"Новое уведомление по ссылке {request.url}:" + '\n' + request.description)
        logger.info("Сообщение отправлено", extra={"recipient_id": request.id, "url": request.url})
    except (FloodWaitError, ChatWriteForbiddenError, MessageTooLongError) as e:
        logger.error("Ошибка при отправке сообщения", extra={"recipient_id": request.id, "url": request.url, "error": str(e)})
        error_data = ApiErrorResponse(
            description="Ошибка при отправке сообщения",
            code="UnknownException",
            exceptionName="UnknownException",
            exceptionMessage=str(e),
            stacktrace=["File 'endpoints.py', line 38, in create"]
        )
        raise ApiErrorException(error_data, status.HTTP_400_BAD_REQUEST)
