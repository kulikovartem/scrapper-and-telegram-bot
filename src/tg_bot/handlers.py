import httpx
import logging
from telethon import events, TelegramClient
from src.tg_settings import TGBotSettings
from src.server_settings import ServerSettings
from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.types import BotCommand, BotCommandScopeDefault
from src.tg_bot.scrapper_client import ScrapperHttpClient
from src.tg_bot.interfaces.scrapper_client import ScrapperClient

logger = logging.getLogger(__name__)
server_settings = ServerSettings()  # type:ignore

STATE_WAIT_TAGS = "WAIT_TAGS"
STATE_WAIT_FILTERS = "WAIT_FILTERS"
user_states = {}

settings = TGBotSettings()  # type:ignore
client = TelegramClient("bot_session", settings.api_id, settings.api_hash)

SCRAPPER_CLIENT: ScrapperClient = ScrapperHttpClient(server_settings.SCRAPPER_IP, server_settings.SCRAPPER_PORT)


async def set_bot_commands() -> None:
    """
    Устанавливает команды для бота в Telegram.

    Этот метод формирует список команд (например, /start, /help, /track, /untrack, /list)
    и отправляет их через метод SetBotCommandsRequest. В случае успеха логируется успешная установка,
    иначе фиксируется ошибка.

    Raises:
        Exception: Любая ошибка, возникающая при установке команд бота.
    """
    commands = [
        BotCommand(command="start", description="Регистрация пользователя"),
        BotCommand(command="help", description="Вывод списка команд"),
        BotCommand(command="track", description="Начать отслеживание ссылки"),
        BotCommand(command="untrack", description="Прекратить отслеживание ссылки"),
        BotCommand(command="list", description="Показать список отслеживаемых ссылок"),
        BotCommand(command="delete", description="Удалить тег у ссылки"),
        BotCommand(command="add", description="Добавить тег к ссылке")
    ]
    try:
        await client(SetBotCommandsRequest(
            commands=commands,
            scope=BotCommandScopeDefault(),
            lang_code=""
        ))
        logger.info("Команды бота успешно установлены", extra={"commands": [cmd.command for cmd in commands]})
    except Exception as e:
        logger.error("Ошибка установки команд бота", extra={"error": str(e)})


@client.on(events.NewMessage(pattern=r'^/'))  # type:ignore
async def unknown_command_handler(event: events.NewMessage) -> None:
    """
    Обрабатывает неизвестные команды.

    Если полученная команда не входит в перечень известных команд (/start, /help, /track, /untrack, /list),
    отправляет сообщение с подсказкой использовать /help. Известные команды игнорируются.

    Args:
        event: Событие Telethon, содержащее информацию о полученном сообщении.
    """
    known_commands = {"/start", "/help", "/track", "/untrack", "/list", "/delete", "/add"}
    command = event.message.message.strip().split()[0]
    if command not in known_commands:
        logger.info("Неизвестная команда", extra={"command": command})
        await event.reply("Неизвестная команда. Используйте /help для получения списка доступных команд.")


@client.on(events.NewMessage(pattern=r'^/start$'))  # type:ignore
async def start_handler(event: events.NewMessage) -> None:
    """
    Обрабатывает команду /start для регистрации пользователя.

    Отправляет POST-запрос к API регистрации, используя идентификатор пользователя (sender_id).
    Если регистрация успешна, отправляет сообщение об успешной регистрации. При ошибке регистрации
    фиксирует ошибку и логирует соответствующее сообщение.

    Args:
        event: Событие Telethon с информацией о сообщении и идентификатором отправителя.
    """
    user_id = event.sender_id
    logger.info("Обработка команды /start", extra={"user_id": user_id})
    message = await SCRAPPER_CLIENT.register(user_id)
    await event.reply(message)


@client.on(events.NewMessage(pattern=r'^/help$'))  # type:ignore
async def help_handler(event: events.NewMessage) -> None:
    """
    Обрабатывает команду /help.

    Отправляет сообщение с описанием доступных команд для пользователя.

    Args:
        event: Событие Telethon, содержащее информацию о сообщении и отправителе.
    """
    logger.info("Обработка команды /help", extra={"user_id": event.sender_id})
    help_text = (
        "/start - регистрация пользователя.\n"
        "/help - вывод списка доступных команд.\n"
        "/track - начать отслеживание ссылки.\n"
        "/untrack - прекратить отслеживание ссылки.\n"
        "/list - показать список отслеживаемых ссылок."
    )
    await event.reply(help_text)

@client.on(events.NewMessage(pattern=r'^/delete(?:\s+(.*))?$'))  # type:ignore
async def delete_tag_handler(event: events.NewMessage) -> None:
    """
    Обработчик команды /delete для удаления тега по заданному имени и URL.

    Принимает сообщение от пользователя, разделяет его на части и выполняет удаление тега,
    если формат сообщения корректен. В случае ошибки отправляется ответ с инструкциями.

    Параметры:
        event (events.NewMessage): Сообщение от пользователя, содержащее команду и параметры.

    Ответ:
        Сообщение пользователю с результатом выполнения операции.
    """
    user_id = event.sender_id
    message_parts = event.message.message.split(maxsplit=2)

    if len(message_parts) < 3:
        await event.reply("Некорректный формат. Используйте: /delete name_tag url")
        return

    tag_name = message_parts[1]
    url = message_parts[2]

    logger.info("Удаление тега", extra={"user_id": user_id, "tag": tag_name, "url": url})

    response = await SCRAPPER_CLIENT.delete_tag(user_id, url, tag_name)

    await event.reply(response)


@client.on(events.NewMessage(pattern=r'^/add(?:\s+(.*))?$'))  # type:ignore
async def add_tag_handler(event: events.NewMessage) -> None:
    """
    Обработчик команды /add для добавления тега по заданному имени и URL.

    Принимает сообщение от пользователя, разделяет его на части и выполняет добавление тега,
    если формат сообщения корректен. В случае ошибки отправляется ответ с инструкциями.

    Параметры:
        event (events.NewMessage): Сообщение от пользователя, содержащее команду и параметры.

    Ответ:
        Сообщение пользователю с результатом выполнения операции.
    """
    user_id = event.sender_id
    message_parts = event.message.message.split(maxsplit=2)

    if len(message_parts) < 3:
        await event.reply("Некорректный формат. Используйте: /add name_tag url")
        return

    tag_name = message_parts[1]
    url = message_parts[2]

    logger.info("Добавление тега", extra={"user_id": user_id, "tag": tag_name, "url": url})

    response = await SCRAPPER_CLIENT.add_tag(user_id, url, tag_name)

    await event.reply(response)

@client.on(events.NewMessage(pattern=r'^/track(?:\s+(.*))?$'))  # type:ignore
async def track_command_handler(event: events.NewMessage) -> None:
    """
    Обрабатывает команду /track для начала отслеживания ссылки.

    Проверяет наличие ссылки в команде. Если ссылка отсутствует, отправляет уведомление о необходимости
    указания ссылки. Если ссылка присутствует, сохраняет состояние пользователя для последующего ввода тегов
    и фильтров, и просит пользователя ввести тэги (или пропустить их, введя "skip").

    Args:
        event: Событие Telethon, содержащее текст сообщения и идентификатор отправителя.
    """
    logger.info("Обработка команды /track", extra={"user_id": event.sender_id})
    command_parts = event.message.message.split(maxsplit=1)
    if len(command_parts) < 2:
        await event.reply("Пожалуйста, укажите ссылку после команды /track")
        logger.warning("Команда /track без ссылки", extra={"user_id": event.sender_id})
        return

    url = command_parts[1].strip()
    user_states[event.sender_id] = {
        "state": STATE_WAIT_TAGS,
        "url": url,
        "tags": [],
        "filters": []
    }
    logger.debug("Состояние для /track установлено", extra={"user_id": event.sender_id, "url": url})
    await event.reply("Введите тэги (опционально) через пробел. Для пропуска пропишите: skip")


@client.on(events.NewMessage)  # type:ignore
async def conversation_handler(event: events.NewMessage) -> None:
    """
    Обрабатывает последовательный ввод пользователя после команды /track.

    В зависимости от текущего состояния (ввод тегов или фильтров), сохраняет введенные данные,
    обновляет состояние пользователя и отправляет соответствующее сообщение с инструкцией.
    Сообщения, начинающиеся с '/', игнорируются.

    Args:
        event: Событие Telethon, содержащее текст сообщения и идентификатор отправителя.
    """

    if event.message.message.startswith('/'):
        return

    state_data = user_states.get(event.sender_id)
    if not state_data:
        return

    if state_data["state"] == STATE_WAIT_TAGS:
        tags_text = event.message.message.strip()
        if tags_text.lower() == "skip":
            state_data["tags"] = []
            logger.info("Пропущены тэги", extra={"user_id": event.sender_id})
        elif tags_text:
            state_data["tags"] = tags_text.split()
            logger.info("Тэги установлены", extra={"user_id": event.sender_id, "tags": state_data["tags"]})
        state_data["state"] = STATE_WAIT_FILTERS
        await event.reply("Настройте фильтры (опционально). Для этого напишите их в формате user:myprofile через пробел. Для пропуска пропишите: skip")
    elif state_data["state"] == STATE_WAIT_FILTERS:
        filters_text = event.message.message.strip()
        if filters_text.lower() == "skip":
            state_data["filters"] = []
            logger.info("Пропущены фильтры", extra={"user_id": event.sender_id})
        elif filters_text:
            state_data["filters"] = filters_text.split()
            logger.info("Фильтры установлены", extra={"user_id": event.sender_id, "filters": state_data["filters"]})
        url = state_data["url"]
        tags = state_data["tags"]
        filters = state_data["filters"]
        payload = {
            "link": url,
            "tags": tags,
            "filters": filters
        }
        headers = {"tg-chat-id": str(event.sender_id)}
        logger.debug("Отправка запроса на добавление ссылки", extra={"user_id": event.sender_id, "payload": payload})
        message = await SCRAPPER_CLIENT.add(payload, headers, event.sender_id, url)
        await event.reply(message)
        del user_states[event.sender_id]


@client.on(events.NewMessage(pattern=r'^/untrack(?:\s+(.*))?$'))  # type:ignore
async def untrack_handler(event: events.NewMessage) -> None:
    """
    Обрабатывает команду /untrack для прекращения отслеживания ссылки.

    Извлекает URL из сообщения и отправляет запрос на удаление ссылки из репозитория.
    Если URL не указан, отправляет уведомление о необходимости его указания.

    Args:
        event: Событие Telethon, содержащее текст сообщения и идентификатор отправителя.
    """
    logger.info("Обработка команды /untrack", extra={"user_id": event.sender_id})
    command_parts = event.message.message.split(maxsplit=1)
    if len(command_parts) < 2:
        await event.reply("Пожалуйста, укажите ссылку для прекращения отслеживания.")
        logger.warning("Команда /untrack без ссылки", extra={"user_id": event.sender_id})
        return

    url = command_parts[1].strip()
    user_id = event.sender_id
    headers = {"tg-chat-id": str(user_id)}
    payload = {"link": url}
    logger.debug("Отправка запроса на удаление ссылки", extra={"user_id": user_id, "link": url})
    message = await SCRAPPER_CLIENT.untrack(payload, headers, user_id, url)
    await event.reply(message)


@client.on(events.NewMessage(pattern=r'^/list$'))  # type:ignore
async def list_handler(event: events.NewMessage) -> None:
    """
    Обрабатывает команду /list для получения списка отслеживаемых ссылок.

    Отправляет GET-запрос к API для получения списка ссылок, ассоциированных с Telegram-чатом,
    идентифицируемым по заголовку запроса. Если ссылки найдены, отправляет их пользователю в виде строки,
    где каждая ссылка отделена символом новой строки. Если список пуст или возникает ошибка, отправляет
    соответствующее сообщение об ошибке.

    Args:
        event: Событие Telethon, содержащее информацию о сообщении и отправителе.

    Raises:
        Логирует и обрабатывает исключения, возникающие при выполнении HTTP-запроса.
    """
    logger.info("Обработка команды /list", extra={"user_id": event.sender_id})
    user_id = event.sender_id
    headers = {"tg-chat-id": str(user_id)}
    message = await SCRAPPER_CLIENT.list(headers, user_id)
    await event.reply(message)
