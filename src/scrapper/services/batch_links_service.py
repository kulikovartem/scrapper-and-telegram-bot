from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.scrapper.factories.client_factory import ClientFactory
from src.scrapper.factories.update_sender_factory import UpdateSenderFactory
from src.scrapper.interfaces.batcher_interface import Batcher
from src.scrapper.interfaces.link_repo_interface import LinkRepo
from src.scrapper.interfaces.update_sender_interface import UpdateSender
from src.scrapper.schemas.link_dto import LinkDTO
from src.scrapper.url_type_definer import URLTypeDefiner
from src.server_settings import ServerSettings

logger = logging.getLogger(__name__)
server_settings = ServerSettings()  # type: ignore


class BatchLinksService(Batcher):
    """
    Сервис пакетной проверки ссылок и отправки уведомлений о новых событиях.

    Алгоритм работы
    ---------------
    1. Делит входной список `LinkDTO` на чанки ≈ 25 % от общего размера.
    2. Для каждой ссылки:
       • определяет её тип,
       • запрашивает свежую информацию у соответствующего клиента,
       • сравнивает дату последнего события с той, что хранится в БД,
       • при расхождении обновляет дату и:
         – если для чата задан `time_push_up` — планирует одноразовое
           уведомление на это время,
         – иначе добавляет ссылку в “горячий” список мгновенной отправки.
    3. Чанки с обновлениями отправляются боту параллельно через
       `UpdateSender` и `ThreadPoolExecutor`.

    Атрибуты класса
    ---------------
    _bot_ip : str
        IP‑адрес REST‑сервиса Telegram‑бота.
    _bot_port : int
        Порт REST‑сервиса Telegram‑бота.
    _update_sender : UpdateSender
        Инкапсулирует HTTP‑запрос к боту.
    _tz : pytz.timezone
        Часовой пояс, в котором работает планировщик.
    _cron_scheduler : AsyncIOScheduler
        Планировщик одноразовых задач (используется для “отложенных”
        уведомлений в заданное `time_push_up`).

    Логирование
    -----------
    * **info**    — ключевые этапы обработки и успешные операции;
    * **debug**   — подробности HTTP‑ответов / полезные данные;
    * **warning** — некорректные пользовательские входы;
    * **error**   — предсказуемые ошибки внешних сервисов;
    * **exception** — непредвиденные исключения.
    """

    _bot_ip: str = server_settings.BOT_IP
    _bot_port: int = server_settings.BOT_PORT
    _update_sender: UpdateSender = UpdateSenderFactory.create_update_sender(
        server_settings.PUSH_TYPE
    )
    _tz = pytz.timezone("Europe/Moscow")
    _cron_scheduler: AsyncIOScheduler = AsyncIOScheduler(timezone=_tz)

    async def batch_links(self, links: list[LinkDTO], repo: LinkRepo) -> None:
        """
        Пакетно обрабатывает список ссылок.

        Параметры
        ----------
        links : list[LinkDTO]
            Ссылки, требующие проверки.
        repo : LinkRepo
            Репозиторий для чтения / записи дат последнего события.

        Логирование
        -----------
        * **info**    — начало / завершение обработки, успешное обновление даты;
        * **error**   — ошибки получения данных от внешних сервисов.
        """
        logger.info(
            "Начало пакетной обработки ссылок",
            extra={"links_count": len(links)},
        )

        if not links:
            logger.info("Ссылок для обработки нет")
            return

        chunk_size = max(1, len(links) // 4)
        chunks = [links[i : i + chunk_size] for i in range(0, len(links), chunk_size)]
        to_send: list[list[tuple[LinkDTO, dict[str, str]]]] = []

        for chunk in chunks:
            links_with_updates: list[tuple[LinkDTO, dict[str, str]]] = []

            for link in chunk:
                url_type = URLTypeDefiner.define(link.link)
                client = ClientFactory.create_client(url_type)

                try:
                    info = await client.get_info_by_url_with_filters(
                        link.link, link.filters
                    )
                    new_date = info["date"]
                    author = info["user"]

                    ignores = [
                        f.split(":", 1)[1] for f in link.filters if f.startswith("ignore:")
                    ]

                    if new_date != link.date and author not in ignores:
                        try:
                            push_up_time = await repo.get_time_push_up(link.tg_id)
                        except Exception as e:
                            logger.exception(
                                "Не удалось получить time_push_up",
                                extra={"tg_id": link.tg_id, "error": str(e)},
                            )
                            push_up_time = None

                        if push_up_time is not None:
                            self._add_cron_task(
                                link.link_id, [(link, info)], push_up_time
                            )
                        else:
                            links_with_updates.append((link, info))

                        await repo.change_date(int(link.link_id), str(new_date))
                        logger.info(
                            "Дата последнего события обновлена",
                            extra={
                                "link_id": link.link_id,
                                "link": link.link,
                                "old_date": link.date,
                                "new_date": new_date,
                            },
                        )

                except Exception as e:
                    logger.error(
                        "Ошибка при получении информации о ссылке",
                        extra={"link": link.link, "error": str(e)},
                    )

            to_send.append(links_with_updates)

        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(self._update_sender.send_update_request, to_send)

        logger.info(
            "Пакетная обработка завершена",
            extra={"links_count": len(links)},
        )

    def start_cron_scheduler(self) -> None:
        """
        Запускает асинхронный планировщик задач APScheduler.

        Логирование
        -----------
        * **info**    — успешный старт;
        * **exception** — ошибки при запуске.
        """
        logger.info("Запуск планировщика задач")
        try:
            self._cron_scheduler.start()
            logger.info("Планировщик задач успешно запущен")
        except Exception as e:
            logger.exception(
                "Ошибка запуска планировщика задач", extra={"error": str(e)}
            )
            raise

    def _add_cron_task(
        self,
        link_id: int,
        links_info: list[tuple[LinkDTO, dict[str, str]]],
        notif_time: time,
    ) -> None:
        """
        Планирует одноразовое уведомление боту на время `notif_time`.

        Параметры
        ----------
        link_id : int
            Идентификатор ссылки (используется для `id` задачи).
        links_info : list[tuple[LinkDTO, dict]]
            Пары *(LinkDTO, свежая‑info)*, которые нужно отправить.
        notif_time : datetime.time
            Локальное время (Europe/Moscow), когда выполнить задачу.

        Логирование
        -----------
        * **info**    — успешное добавление задачи;
        * **exception** — ошибки при добавлении.
        """
        today = date.today()
        run_dt = self._tz.localize(datetime.combine(today, notif_time))

        if run_dt < datetime.now(self._tz):
            run_dt += timedelta(days=1)

        logger.info(
            "Планирование задачи отправки уведомления",
            extra={
                "task_id": f"one_shot_{link_id}",
                "run_datetime": run_dt.isoformat(),
                "links_count": len(links_info),
            },
        )

        try:
            self._cron_scheduler.add_job(
                self._update_sender.send_update_request,
                trigger="date",
                run_date=run_dt,
                args=[links_info],
                id=f"one_shot_{link_id}",
                replace_existing=True,
                misfire_grace_time=300,
            )
            logger.info(
                "Задача успешно добавлена в планировщик",
                extra={"task_id": f"one_shot_{link_id}"},
            )
        except Exception as e:
            logger.exception(
                "Ошибка добавления задачи в планировщик",
                extra={"task_id": f"one_shot_{link_id}", "error": str(e)},
            )
