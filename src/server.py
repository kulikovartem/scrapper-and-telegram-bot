import logging
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
import src.bot.endpoints as botapi
import src.scrapper.endpoints as sc
import src.scrapper.exceptions as scr_exceptions
import src.bot.exceptions.api_error_exception as bot_exceptions
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

bot = FastAPI(title="bot api")
scrapper = FastAPI(title="scrapper")

bot.include_router(router=botapi.bot_router, prefix="/api/v1")
scrapper.include_router(router=sc.scrapper_router, prefix="/api/v1")


@scrapper.exception_handler(scr_exceptions.ApiErrorException)
async def scrapper_api_exception_error_handler(request: Request, exc: scr_exceptions.ApiErrorException) -> JSONResponse:
    """
    Обработчик исключений для API скраппера.

    Args:
        request (Request): Запрос, при котором возникло исключение.
        exc (ApiErrorException): Исключение, содержащее информацию об ошибке.

    Returns:
        JSONResponse: Ответ с кодом ошибки и данными об ошибке.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.model.model_dump(),
    )


@bot.exception_handler(bot_exceptions.ApiErrorException)
async def bot_api_exception_exception_error_handler(request: Request,
                                                    exc: scr_exceptions.ApiErrorException) -> JSONResponse:
    """
    Обработчик исключений для API бота.

    Args:
        request (Request): Запрос, при котором возникло исключение.
        exc (ApiErrorException): Исключение, содержащее информацию об ошибке.

    Returns:
        JSONResponse: Ответ с кодом ошибки и данными об ошибке.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.model.model_dump()
    )


bot.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scrapper.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
