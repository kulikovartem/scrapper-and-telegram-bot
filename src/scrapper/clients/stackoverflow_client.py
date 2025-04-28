import re
import httpx
import logging
from typing import Dict
from datetime import datetime
from typing import List
from src.scrapper.interfaces.client_interface import Client
from src.scrapper.exceptions.url_is_not_supported_exception import UrlIsNotSupportedException
from src.scrapper.exceptions.resource_is_not_found_exception import ResourceIsNotFoundException
from src.scrapper.exceptions.not_successful_response_exception import NotSuccessfulResponseException
from src.scrapper.exceptions.not_supported_type_of_filter_exception import NotSupportedTypeOfFilter

logger = logging.getLogger(__name__)


class StackOverflowClient(Client):
    """
    Клиент для работы с API StackOverflow.

    Этот класс предоставляет методы для получения информации о вопросах на StackOverflow с учетом
    фильтров, а также получения последней активности в вопросах, включая ответы и комментарии.
    Метод `get_info_by_url_with_filters` принимает URL вопроса на StackOverflow и фильтры, проверяет корректность URL,
    извлекает необходимые параметры и отправляет запрос к API StackExchange для получения данных о вопросе,
    его последней активности, а также ответах и комментариях.

    Атрибуты:
        _pattern (str): Регулярное выражение для проверки корректности URL вопроса на StackOverflow.

    Методы:
        get_info_by_url_with_filters(url: str, filters: List[str]) -> Dict[str, str]:
            Получает информацию о вопросе по URL с учетом фильтров.

        _get_question_info(question_id: str, filters: List[str]) -> Dict[str, str]:
            Выполняет запрос к API StackExchange для получения информации о вопросе, ответах и комментариях.

        _convert_timestamp_to_date(timestamp: int) -> str:
            Преобразует метку времени Unix в строку даты и времени в формате '%Y-%m-%d %H:%M:%S'.
    """

    _pattern: str = r"^https:\/\/stackoverflow\.com\/questions\/(\d+)\/?.*$"

    async def get_info_by_url_with_filters(self, url: str, filters: List[str]) -> Dict[str, str]:
        """
        Получает информацию о вопросе StackOverflow с учетом фильтров.

        Этот метод извлекает идентификатор вопроса из URL и выполняет запрос к API StackOverflow для получения
        информации о вопросе, включая его заголовок, пользователя, дату и предварительный текст. Также включает
        информацию о последней активности (ответах и комментариях) по этому вопросу.

        Args:
            url (str): URL вопроса на StackOverflow, например "https://stackoverflow.com/questions/1234567/question-title".
            filters (List[str]): Список фильтров в формате "ключ:значение" для уточнения запроса.

        Returns:
            Dict[str, str]: Словарь с информацией о вопросе, включая:
                - "title": Заголовок вопроса.
                - "user": Имя пользователя, который создал вопрос или последний ответил.
                - "date": Дата и время создания или последней активности.
                - "preview": Краткий фрагмент текста вопроса, ответа или комментария.

        Raises:
            UrlIsNotSupportedException: Если URL не соответствует формату StackOverflow.
            NotSupportedTypeOfFilter: Если один из фильтров имеет неверный формат.
            ResourceIsNotFoundException: Если вопрос с заданным ID не найден.
            NotSuccessfulResponseException: Если API возвращает неуспешный статус ответа.
        """
        logger.debug("Получение информации о вопросе", extra={"url": url, "filters": filters})
        pattern_match = re.match(self._pattern, url)
        if pattern_match:
            question_id = pattern_match.group(1)
            logger.debug("Извлечён question_id", extra={"question_id": question_id})
            return await self._get_question_info(question_id, filters)
        else:
            logger.error("Неподдерживаемый формат ссылки", extra={"url": url})
            raise UrlIsNotSupportedException(f"Ссылка {url} не поддерживается.")

    async def _get_question_info(self, question_id: str, filters: List[str]) -> Dict[str, str]:
        """
        Получает подробную информацию о вопросе, включая последние ответы и комментарии.

        Этот метод отправляет запрос к API StackExchange для получения информации о заданном вопросе, включая
        его заголовок, владельца, дату создания, а также последние ответы и комментарии.

        Args:
            question_id (str): Идентификатор вопроса.
            filters (List[str]): Список фильтров для уточнения запроса.

        Returns:
            Dict[str, str]: Словарь с информацией о вопросе и активности:
                - "title": Заголовок вопроса.
                - "user": Имя последнего активного пользователя.
                - "date": Дата и время последней активности.
                - "preview": Краткий фрагмент ответа или комментария.

        Raises:
            ResourceIsNotFoundException: Если вопрос не найден по заданному ID.
            NotSuccessfulResponseException: Если API возвращает неуспешный статус ответа.
        """
        url = f"https://api.stackexchange.com/2.3/questions/{question_id}"
        params = {"site": "stackoverflow", "filter": "withbody"}

        if filters:
            for f in filters:
                if ":" in f:
                    key, value = f.split(":", 1)
                    params[key] = value
                    logger.debug("Добавлен фильтр", extra={"key": key, "value": value})
                else:
                    logger.error("Неправильный формат фильтра", extra={"filter": f})
                    raise NotSupportedTypeOfFilter(f"Фильтр {f} не в правильном формате.")

        logger.debug("Отправка запроса к StackExchange", extra={"url": url, "params": params})
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            logger.debug("Получен ответ", extra={"status_code": response.status_code, "response": response.text})
            if response.status_code == 200:
                data = response.json()
                if "items" in data and data["items"]:
                    question = data["items"][0]
                    result = {
                        "title": question["title"],
                        "user": question["owner"]["display_name"],
                        "date": self._convert_timestamp_to_date(question["creation_date"]),
                        "preview": question.get("body", "")[:200],
                    }

                    answers_url = f"https://api.stackexchange.com/2.3/questions/{question_id}/answers"
                    comments_url = f"https://api.stackexchange.com/2.3/questions/{question_id}/comments"
                    last_message = result["preview"]
                    last_timestamp = question["creation_date"]

                    async with httpx.AsyncClient() as client:
                        ans_response = await client.get(answers_url,
                                                        params={"site": "stackoverflow", "sort": "creation",
                                                                "order": "desc", "filter": "withbody"})
                        if ans_response.status_code == 200:
                            ans_data = ans_response.json()
                            if "items" in ans_data and ans_data["items"]:
                                answer = ans_data["items"][0]
                                if answer["creation_date"] > last_timestamp:
                                    last_timestamp = answer["creation_date"]
                                    last_message = answer.get("body", "")[:200]
                                    result["user"] = answer["owner"]["display_name"]
                                    result["preview"] = last_message
                                    result["date"] = self._convert_timestamp_to_date(answer["creation_date"])

                        com_response = await client.get(comments_url,
                                                        params={"site": "stackoverflow", "sort": "creation",
                                                                "order": "desc", "filter": "withbody"})
                        if com_response.status_code == 200:
                            com_data = com_response.json()
                            if "items" in com_data and com_data["items"]:
                                comment = com_data["items"][0]
                                if comment["creation_date"] > last_timestamp:
                                    last_timestamp = comment["creation_date"]
                                    last_message = comment.get("body", "")[:200]
                                    result["user"] = comment["owner"]["display_name"]
                                    result["preview"] = last_message
                                    result["date"] = self._convert_timestamp_to_date(comment["creation_date"])

                    logger.info("Информация о вопросе получена", extra=result)
                    return result
                else:
                    logger.error("Вопрос не найден", extra={"question_id": question_id})
                    raise ResourceIsNotFoundException(f"Вопрос с id {question_id} не найден.")
            else:
                logger.error("Ошибка запроса к API StackExchange", extra={"status_code": response.status_code})
                raise NotSuccessfulResponseException(f"Response with status code: {response.status_code}.")

    def _convert_timestamp_to_date(self, timestamp: int) -> str:
        """
        Преобразует метку времени Unix в строку даты и времени в формате '%Y-%m-%d %H:%M:%S'.

        Args:
            timestamp (int): Метка времени Unix.

        Returns:
            str: Дата и время в формате '%Y-%m-%d %H:%M:%S', например "2025-04-01 19:56:41".
        """
        try:
            return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return "Undefined"
