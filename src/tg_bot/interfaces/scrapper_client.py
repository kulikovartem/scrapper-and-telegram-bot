from typing import Protocol, Dict


class ScrapperClient(Protocol):
    """
    Интерфейс для клиентов, взаимодействующих со Scrapper API.

    Классы, реализующие данный интерфейс, должны предоставлять асинхронные методы для регистрации пользователя,
    добавления/удаления ссылок, управления тегами и получения списка всех отслеживаемых ссылок.

    Методы:
        async register(user_id: int) -> str:
            Регистрирует пользователя по идентификатору `user_id` в системе Scrapper.

        async add(payload: Dict[str, str], headers: Dict[str, str], sender_id: int, url: str) -> str:
            Добавляет новую ссылку в систему Scrapper.

        async untrack(payload: Dict[str, str], headers: Dict[str, str], user_id: int, url: str) -> str:
            Удаляет указанную ссылку из системы Scrapper.

        async list(headers: Dict[str, str], user_id: int) -> str:
            Возвращает список отслеживаемых ссылок для заданного пользователя, включая группировку по тегам.

        async delete_tag(user_id: int, url: str, tag_name: str) -> str:
            Удаляет указанный тег у заданной ссылки.

        async add_tag(user_id: int, url: str, tag_name: str) -> str:
            Добавляет новый тег к указанной ссылке.
    """

    async def register(self, user_id: int) -> str:
        pass

    async def add(self, payload: Dict[str, str], headers: Dict[str, str],
                  sender_id: int, url: str) -> str:
        pass

    async def untrack(self, payload: Dict[str, str], headers: Dict[str, str], user_id: int, url: str) -> str:
        pass

    async def list(self, headers: Dict[str, str], user_id: int) -> str:
        pass

    async def delete_tag(self, user_id: int, url: str, tag_name: str) -> str:
        pass

    async def add_tag(self, user_id: int, url: str, tag_name: str) -> str:
        pass

    async def change_push_up_time(self, user_id: int, time: str | None) -> str:
        pass
