import argparse
import asyncio
import uvicorn
from src.server import bot, scrapper
from src.tg_bot.handlers import client, settings
from src.tg_bot.handlers import set_bot_commands
from src.server_settings import ServerSettings
from src.scrapper.services.scheduler import Scheduler
from src.bot.endpoints import client as tg_bot_client
from src.bot.services.push_up_consumer import PushUpConsumer
import src.log_config

server_settings = ServerSettings()  # type: ignore

async def start_push_up_consumer() -> None:
    consumer = PushUpConsumer()
    await consumer.start()

async def start_client_for_bot() -> None:
    await tg_bot_client.start(bot_token=settings.token)

async def start_tg_client() -> None:
    await client.start(bot_token=settings.token)
    await set_bot_commands()
    await client.run_until_disconnected()


async def start_bot() -> None:
    config_bot = uvicorn.Config(app=bot, host=server_settings.BOT_IP, port=server_settings.BOT_PORT, log_level="info")
    server_bot = uvicorn.Server(config_bot)
    await server_bot.serve()


async def start_scrapper() -> None:
    config_scrapper = uvicorn.Config(app=scrapper, host=server_settings.SCRAPPER_IP, port=server_settings.SCRAPPER_PORT, log_level="info")
    server_scrapper = uvicorn.Server(config_scrapper)
    await server_scrapper.serve()


async def start_scheduler() -> None:
    scheduler = Scheduler()
    await scheduler.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start services.")
    parser.add_argument(
        "--services",
        type=str,
        default="all",
        help="Comma-separated list of services to start: bot, scrapper, telethon, scheduler, or all"
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    services = args.services.split(",")

    if "all" in services:
        services = ["scrapper", "tg_client", "scheduler"]

    tasks = []
    if "scrapper" in services:
        tasks.append(start_scrapper())
    if "tg_client" in services:
        tasks.append(start_tg_client())
    if "scheduler" in services:
        tasks.append(start_scheduler())
    if server_settings.PUSH_TYPE == "HTTP":
        tasks.append(start_bot())
    elif server_settings.PUSH_TYPE == "KAFKA":
        asyncio.create_task(start_push_up_consumer())
    tasks.append(start_client_for_bot())

    if not tasks:
        print("Не указано, какие сервисы запускать. Укажите --services или используйте --services=all.")
        return

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
