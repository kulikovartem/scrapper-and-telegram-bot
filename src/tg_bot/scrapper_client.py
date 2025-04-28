import httpx
import logging
from typing import Dict
from collections import defaultdict
from src.tg_bot.interfaces.scrapper_client import ScrapperClient

logger = logging.getLogger(__name__)


class ScrapperHttpClient(ScrapperClient):

    """
    Класс для взаимодействия с API Scrapper для управления ссылками и тегами.

    Этот класс предоставляет методы для регистрации пользователя, добавления и удаления ссылок,
    а также для работы с тегами, включая добавление и удаление тегов у ссылок.

    Атрибуты:
        scrapper_ip (str): IP-адрес сервера Scrapper.
        scrapper_port (int): Порт сервера Scrapper.
        _base_url (str): Полный адрес сервера Scrapper.

    Методы:
        register(user_id: int) -> str:
            Регистрирует пользователя по указанному ID.

        add(payload: Dict[str, str], headers: Dict[str, str], sender_id: int, url: str) -> str:
            Добавляет новую ссылку с указанными данными.

        untrack(payload: Dict[str, str], headers: Dict[str, str], user_id: int, url: str) -> str:
            Удаляет ссылку из отслеживаемых.

        list(headers: Dict[str, str], user_id: int) -> str:
            Получает список отслеживаемых ссылок и группирует их по тегам.

        delete_tag(user_id: int, url: str, tag_name: str) -> str:
            Удаляет тег с указанной ссылки.

        add_tag(user_id: int, url: str, tag_name: str) -> str:
            Добавляет тег к указанной ссылке.
    """

    scrapper_ip: str
    scrapper_port: int

    def __init__(self, ip: str, port: int):
        self.scrapper_ip = ip
        self.scrapper_port = port

    @property
    def _base_url(self) -> str:
        return f"http://{self.scrapper_ip}:{self.scrapper_port}"

    async def register(self, user_id: int) -> str:
        """
        Регистрирует пользователя с заданным user_id.

        Аргументы:
        user_id (int): Идентификатор пользователя.

        Возвращает:
        str: Сообщение о результате регистрации пользователя.
        """
        async with httpx.AsyncClient() as async_client:
            try:
                response = await async_client.post(
                    self._base_url + f"/api/v1/tg-chat/{user_id}"
                )
                logger.debug("Ответ от API регистрации",
                             extra={"status_code": response.status_code, "response": response.text})
                if response.status_code == 200:
                    logger.info("Пользователь зарегистрирован", extra={"user_id": user_id})
                    return "Вы успешно зарегистрированы!"
                else:
                    data = response.json()
                    logger.error("Ошибка регистрации пользователя", extra={"user_id": user_id, "response": data})
                    message = data.get("description", "Ошибка при регистрации пользователя.")
                    return str(message)
            except Exception as e:
                logger.exception("Исключение при регистрации пользователя", extra={"user_id": user_id, "error": str(e)})
                return "Ошибка регистрации пользователя"

    async def add(self, payload: Dict[str, str], headers: Dict[str, str],
                  sender_id: int, url: str) -> str:
        """
        Добавляет новую ссылку для отслеживания.

        Аргументы:
        payload (Dict[str, str]): Данные ссылки для добавления.
        headers (Dict[str, str]): Заголовки запроса.
        sender_id (int): Идентификатор отправителя.
        url (str): URL, который добавляется для отслеживания.

        Возвращает:
        str: Сообщение о результате добавления ссылки.
        """
        async with httpx.AsyncClient() as async_client:
            try:
                response = await async_client.post(
                    self._base_url + "/api/v1/links",
                    json=payload,
                    headers=headers
                )
                logger.debug("Ответ от API добавления ссылки", extra={"status_code": response.status_code, "response": response.text})
                if response.status_code == 200:
                    logger.info("Ссылка добавлена", extra={"user_id": sender_id, "url": url})
                    return "Ссылка успешно добавлена."
                else:
                    data = response.json()
                    message = data.get("description", "Ошибка при добавлении ссылки. Проверьте введенные данные!")
                    logger.error("Ошибка при добавлении ссылки", extra={"user_id": sender_id, "payload": payload,
                                                                        "response": data})
                    return str(message)
            except Exception as e:
                logger.exception("Исключение при добавлении ссылки", extra={"user_id": sender_id, "error": str(e)})
                return "Ошибка при добавлении ссылки"

    async def untrack(self, payload: Dict[str, str], headers: Dict[str, str], user_id: int, url: str) -> str:
        """
        Удаляет ссылку из отслеживаемых.

        Аргументы:
        payload (Dict[str, str]): Данные ссылки для удаления.
        headers (Dict[str, str]): Заголовки запроса.
        user_id (int): Идентификатор пользователя.
        url (str): URL, который удаляется из отслеживания.

        Возвращает:
        str: Сообщение о результате удаления ссылки.
        """
        async with httpx.AsyncClient() as async_client:
            try:
                response = await async_client.request(
                    "DELETE",
                    self._base_url + "/api/v1/links",
                    json=payload,
                    headers=headers
                )
                logger.debug("Ответ от API удаления ссылки",
                             extra={"status_code": response.status_code, "response": response.text})
                if response.status_code == 200:
                    logger.info("Ссылка удалена", extra={"user_id": user_id, "link": url})
                    return f"Ссылка {url} успешно удалена из отслеживаемых."
                else:
                    data = response.json()
                    logger.error("Ошибка при удалении ссылки",
                                 extra={"user_id": user_id, "link": url, "response": data})
                    message = data.get("description", "Ошибка при удалении ссылки. Проверьте введенные данные!")
                    return str(message)
            except Exception as e:
                logger.exception("Исключение при удалении ссылки",
                                 extra={"user_id": user_id, "link": url, "error": str(e)})
                return "Ошибка при удалении ссылки"

    async def list(self, headers: Dict[str, str], user_id: int) -> str:
        """
        Получает список отслеживаемых ссылок и группирует их по тегам.

        Аргументы:
        headers (Dict[str, str]): Заголовки запроса.
        user_id (int): Идентификатор пользователя.

        Возвращает:
        str: Список отслеживаемых ссылок, сгруппированных по тегам.
        """
        async with httpx.AsyncClient() as async_client:
            try:
                group_by_tags = defaultdict(list)

                response = await async_client.get(
                    self._base_url + "/api/v1/links",
                    headers=headers
                )
                logger.debug("Ответ от API получения списка ссылок",
                             extra={"status_code": response.status_code, "response": response.text})
                if response.status_code == 200:
                    data = response.json()
                    links = data.get("links")
                    for link in links:
                        tags = link.get("tags")
                        if tags:
                            for tag in tags:
                                group_by_tags[tag].append(link.get("url"))
                        else:
                            group_by_tags["Без тегов"].append(link.get("url"))
                    if group_by_tags:
                        result = []
                        for tag, links in group_by_tags.items():
                            links_str = "\n".join(links)
                            result.append(f"{tag}:\n{links_str}\n")
                        logger.info("Список ссылок отправлен", extra={"user_id": user_id, "links": result})
                        return ''.join(result)
                    else:
                        logger.info("Отслеживаемых ссылок не найдено", extra={"user_id": user_id})
                        return "Нет отслеживаемых ссылок"
                else:
                    data = response.json()
                    message = data.get("description", "Ошибка при получении ссылок.")
                    logger.error("Ошибка получения списка ссылок", extra={"user_id": user_id, "response": data})
                    return str(message)
            except Exception as e:
                logger.exception("Исключение при получении списка ссылок", extra={"user_id": user_id, "error": str(e)})
                return "Ошибка получения списка ссылок"

    async def delete_tag(self, user_id: int, url: str, tag_name: str) -> str:
        """
        Удаляет тег у ссылки.

        Аргументы:
        user_id (int): Идентификатор пользователя.
        url (str): URL, с которого удаляется тег.
        tag_name (str): Название тега для удаления.

        Возвращает:
        str: Сообщение о результате удаления тега.
        """
        headers = {"tg-chat-id": str(user_id)}
        payload = {"url": url, "tag": tag_name}
        async with httpx.AsyncClient() as async_client:
            try:
                response = await async_client.request(
                    "DELETE",
                    self._base_url + "/api/v1/tags",
                    json=payload,
                    headers=headers
                )
                logger.debug("Ответ от API удаления тега у ссылки",
                             extra={"status_code": response.status_code, "response": response.text})
                if response.status_code == 200:
                    logger.info("Тег у ссылки удален", extra={"user_id": user_id, "link": url, "tag": tag_name})
                    return f"Тег {tag_name} у ссылки {url} успешно удален."
                else:
                    data = response.json()
                    logger.error("Ошибка при удалении тега у ссылки",
                                 extra={"user_id": user_id, "link": url, "tag": tag_name, "response": data})
                    message = data.get("description", "Ошибка при удалении тега у ссылки. Проверьте введенные данные!")
                    return str(message)
            except Exception as e:
                logger.exception("Исключение при удалении ссылки",
                                 extra={"user_id": user_id, "link": url, "tag": tag_name, "error": str(e)})
                return "Ошибка при удалении тега у ссылки"

    async def add_tag(self, user_id: int, url: str, tag_name: str) -> str:
        """
        Добавляет тег к ссылке.

        Аргументы:
        user_id (int): Идентификатор пользователя.
        url (str): URL, к которому добавляется тег.
        tag_name (str): Название тега для добавления.

        Возвращает:
        str: Сообщение о результате добавления тега.
        """
        headers = {"tg-chat-id": str(user_id)}
        payload = {"url": url, "tag": tag_name}
        async with httpx.AsyncClient() as async_client:
            try:
                response = await async_client.post(
                    self._base_url + "/api/v1/tags",
                    json=payload,
                    headers=headers
                )
                logger.debug("Ответ от API добавления тега",
                             extra={"status_code": response.status_code, "response": response.text})
                if response.status_code == 200:
                    logger.info("Тег добавлен к ссылке", extra={"user_id": user_id, "link": url, "tag": tag_name})
                    return f"Тег {tag_name} успешно добавлен к ссылке {url}."
                else:
                    data = response.json()
                    logger.error("Ошибка при добавлении тега",
                                 extra={"user_id": user_id, "link": url, "tag": tag_name, "response": data})
                    message = data.get("description", "Ошибка при добавлении тега. Проверьте введенные данные!")
                    return str(message)
            except Exception as e:
                logger.exception("Исключение при добавлении тега",
                                 extra={"user_id": user_id, "link": url, "tag": tag_name, "error": str(e)})
                return "Ошибка при добавлении тега."
