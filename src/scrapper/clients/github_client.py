import logging
import re
import httpx
from src.scrapper.interfaces.client_interface import Client
from src.scrapper.exceptions import UrlIsNotSupportedException
from src.scrapper.exceptions import ResourceIsNotFoundException
from src.scrapper.exceptions import NotSuccessfulResponseException
from src.scrapper.exceptions import NotSupportedTypeOfFilter

logger = logging.getLogger(__name__)


class GitHubClient(Client):
    """
    Клиент для работы с GitHub API.

    Данный класс реализует методы для получения информации о последних коммитах
    из репозитория GitHub. Метод get_date_by_url_with_filters проверяет корректность URL,
    извлекает необходимые параметры и отправляет запрос к API GitHub для получения данных последнего коммита.
    """

    _pattern: str = r"^https:\/\/github\.com\/([^\/]+)\/([^\/]+)\/commits(\/[^\/]+)?\/?$"

    async def get_info_by_url_with_filters(self, url: str, filters: list[str]) -> dict[str, str]:
        """
        Получает информацию о последнем коммите для заданного URL репозитория GitHub с учетом фильтров.

        Args:
            url (str): URL репозитория GitHub, например "https://github.com/owner/repo/commits".
            filters (List[str]): Список фильтров в формате "ключ:значение".

        Returns:
            Dict[str, str]: Словарь с информацией о последнем коммите.

        Raises:
            UrlIsNotSupportedException: Если переданный URL не соответствует ожидаемому формату.
            NotSupportedTypeOfFilter: Если один из фильтров имеет неверный формат.
            ResourceIsNotFoundException: Если API возвращает успешный ответ, но в репозитории отсутствуют коммиты.
            NotSuccessfulResponseException: Если API возвращает код ответа, отличный от 200.
        """
        logger.debug("Получение данных коммита", extra={"url": url, "filters": filters})
        pattern_match = re.match(self._pattern, url)
        if pattern_match:
            owner = pattern_match.group(1)
            repo = pattern_match.group(2)
            return await self._get_latest_commit_info(owner, repo, filters)
        else:
            logger.error("Неподдерживаемый формат ссылки", extra={"url": url})
            raise UrlIsNotSupportedException(f"Ссылка {url} не поддерживается.")

    async def _get_latest_commit_info(self, owner: str, repo: str, filters: list[str]) -> dict[str, str]:
        """
        Выполняет запрос к GitHub API для получения информации о последнем коммите в репозитории.

        Args:
            owner (str): Имя владельца репозитория.
            repo (str): Имя репозитория.
            filters (List[str]): Список фильтров в формате "ключ:значение".

        Returns:
            Dict[str, str]: Словарь с информацией о последнем коммите.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        params = {}
        if filters:
            for f in filters:
                if ":" in f:
                    key, value = f.split(":", 1)
                    params[key] = value
                else:
                    logger.error("Неподдерживаемый фильтр", extra={"filter": f})
                    raise NotSupportedTypeOfFilter(f"Фильтр {f} не поддерживается.")
        logger.debug("Отправка запроса к GitHub", extra={"url": url, "params": params})
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            logger.debug("Получен ответ", extra={"status_code": response.status_code, "response": response.text})
            try:
                response.raise_for_status()
                commits = response.json()
                if commits:
                    latest_commit = commits[0]
                    commit_message = latest_commit["commit"]["message"]
                    commit_date = self._convert_date(latest_commit["commit"]["author"]["date"])
                    author_name = latest_commit["commit"]["author"]["name"]
                    logger.info("Успешно получена информация о коммите", extra={"commit_date": commit_date})
                    return {
                        "commit message": commit_message,
                        "user": author_name,
                        "date": commit_date,
                    }
                else:
                    logger.error("Нет коммитов", extra={"owner": owner, "repo": repo})
                    raise ResourceIsNotFoundException(
                        f"Нет коммитов в репозитории {repo} пользователя {owner}."
                    )
            except httpx.HTTPStatusError:
                logger.error("Ошибка запроса к API GitHub", extra={"status_code": response.status_code})
                raise NotSuccessfulResponseException(f"Response with status code: {response.status_code}.")

    def _convert_date(self, date: str) -> str:
        """
                Преобразует строку даты в формат без символов 'T' и 'Z'.

                Этот метод принимает строку даты в формате ISO 8601, где символ 'T' разделяет
                дату и время, а символ 'Z' обозначает время в UTC. Метод удаляет символ 'T'
                и 'Z' для удобства дальнейшего использования.

                Args:
                    date (str): Строка с датой и временем в формате ISO 8601, например "2025-04-01T19:56:41Z".

                Returns:
                    str: Строка с преобразованной датой и временем, например "2025-04-01 19:56:41".
        """
        return date.replace('T', ' ').replace('Z', '')
