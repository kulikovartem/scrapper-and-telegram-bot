from src.scrapper.clients.github_client import GitHubClient
from src.scrapper.clients.stackoverflow_client import StackOverflowClient
from src.scrapper.interfaces.client_interface import Client
from src.scrapper.exceptions.url_is_not_supported_exception import UrlIsNotSupportedException


class ClientFactory:
    """
    Фабрика клиентов для работы с внешними сервисами.

    Данный класс предоставляет статический метод для создания клиента (объекта, реализующего интерфейс Client)
    в зависимости от типа переданного URL или доменного имени. Поддерживаются клиенты для GitHub и StackOverflow.
    Если переданный тип не поддерживается, выбрасывается исключение UrlIsNotSupportedException.
    """

    @staticmethod
    def create_client(client_type: str) -> Client:
        """
        Создает и возвращает клиента для заданного типа сервиса.

        Args:
            client_type (str): Строковое представление типа клиента, например "github.com" или "stackoverflow.com".

        Returns:
            Client: Объект клиента, соответствующий заданному типу.

        Raises:
            UrlIsNotSupportedException: Если переданный тип клиента не поддерживается.
        """
        match client_type:
            case "github.com":
                return GitHubClient()
            case "stackoverflow.com":
                return StackOverflowClient()
            case _:
                raise UrlIsNotSupportedException(f"Тип клиента не поддерживается {client_type}.")
