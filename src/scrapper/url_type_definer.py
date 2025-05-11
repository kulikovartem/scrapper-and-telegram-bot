from src.scrapper.exceptions import UrlIsNotSupportedException


class URLTypeDefiner:
    """
    Класс для определения типа URL. Этот класс используется для идентификации различных типов URL
    на основе их доменов (например, github.com, stackoverflow.com) и выбрасывает исключение, если тип не поддерживается.

    Методы:
        define(url: str) -> str: Определяет тип URL на основе домена ссылки.
    """

    @staticmethod
    def define(url: str) -> str:
        """
        Определяет тип URL на основе домена. Поддерживаются следующие домены: github.com, stackoverflow.com.

        Параметры:
            url (str): URL для определения типа.

        Возвращает:
            str: Тип URL, соответствующий домену.

        Исключения:
            UrlIsNotSupportedException: Если URL не поддерживается.

        Пример:
            >>> URLTypeDefiner.define("https://github.com/example/repo")
            'github.com'

            >>> URLTypeDefiner.define("https://example.com")
            UrlIsNotSupportedException: Ссылка не поддерживается: https://example.com
        """
        match url:
            case _ if "github.com" in url:
                return "github.com"
            case _ if "stackoverflow.com" in url:
                return "stackoverflow.com"
            case _:
                raise UrlIsNotSupportedException(f"Ссылка не поддерживается: {url}")
