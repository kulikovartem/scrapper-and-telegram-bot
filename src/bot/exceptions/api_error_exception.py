from src.bot.schemas.api_error_response import ApiErrorResponse


class ApiErrorException(Exception):
    """
    Исключение для представления ошибок API.

    Это исключение используется для формирования структурированного ответа об ошибке,
    который содержит детальную информацию о возникшей проблеме.

    Attributes:
        model (ApiErrorResponse): Модель, описывающая ошибку, включая описание, код ошибки,
                                  имя исключения, сообщение и трассировку стека.
        status_code (int): HTTP-статус код, который следует вернуть клиенту.
    """
    def __init__(self, model: ApiErrorResponse, status_code: int):
        """
        Инициализирует исключение ApiErrorException.

        Args:
            model (ApiErrorResponse): Объект модели ошибки, содержащий подробности об ошибке.
            status_code (int): HTTP-статус код, который будет использован в ответе.
        """
        self.model = model
        self.status_code = status_code
