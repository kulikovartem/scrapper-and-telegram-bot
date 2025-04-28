from src.scrapper.schemas.api_error_response import ApiErrorResponse


class ApiErrorException(Exception):
    """
    Исключение для представления ошибок API.

    Это исключение используется для формирования структурированного ответа об ошибке,
    содержащего подробную информацию о проблеме, возникшей в процессе обработки запроса API.

    Атрибуты:
        model (ApiErrorResponse): Модель ошибки, включающая описание, код ошибки, имя и сообщение исключения, а также стек вызовов.
        status_code (int): HTTP-статус код, который следует вернуть клиенту.
    """
    def __init__(self, model: ApiErrorResponse, status_code: int):
        """
        Инициализирует ApiErrorException.

        Args:
            model (ApiErrorResponse): Объект, содержащий подробности ошибки.
            status_code (int): HTTP-статус код ошибки.
        """
        self.model = model
        self.status_code = status_code
