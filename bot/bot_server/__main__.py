from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Sequence

import httpx
# import sentry_sdk
import uvloop

from aiogram.enums import ChatType
from aiogram.filters import BaseFilter
from aiogram.types import Message
from loguru import logger

from bot_server.core.config import settings
from bot_server.core.loader import app, bot, dp
from bot_server.handlers import get_handlers_router
from bot_server.handlers.metrics import MetricsView
from bot_server.keyboards.default_commands import remove_default_commands, set_default_commands
from bot_server.keyboards.inline.task import task_keyboard
from bot_server.middlewares import register_middlewares
from bot_server.middlewares.prometheus import prometheus_middleware_factory
from bot_server.services.users import get_user_by_camunda_user_id
from bot_server.utils.decorators import HealthCheck
from camunda_client import CamundaEngineClient
from camunda_client.clients.dto import AuthData


# from sentry_sdk.integrations import httpx
# from sentry_sdk.integrations.loguru import LoggingLevels, LoguruIntegration

if settings.USE_WEBHOOK:
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
    from aiohttp import web


async def fetch_camunda_tasks() -> Sequence[dict]:
    pass # till user
    # async with httpx.AsyncHTTPTransport() as transport:
    #
    #     camunda_client = CamundaEngineClient(
    #         auth_data=AuthData(username=settings.ENGINE_USERNAME, password=settings.ENGINE_PASSWORD),
    #         base_url=settings.ENGINE_URL,
    #         transport=transport,
    #     )
    #     tasks = await camunda_client.get_tasks()
    #     tasks_to_ping = []
    #
    #     for task in tasks:
    #         async with sessionmaker() as session:
    #             user = await get_user_by_camunda_user_id(session, task.assignee)
    #
    #         variables = await camunda_client.get_variable_instances(process_instance_id=task.process_instance_id)
    #         tasks_to_ping.append({"task": task,
    #                               "id": task.id,
    #                               "name": task.name,
    #                               "telegram_user_id": user.telegram_user_id if user else None,
    #                               "variables": variables
    #                               })
    #     return tasks_to_ping


@HealthCheck
async def fetch_camunda_task_and_send_notification() -> dict:
    # Assume you have a list of user IDs to poll tasks for
    tasks = await fetch_camunda_tasks()
    if tasks:
        tasks_dict = defaultdict(list)
        for task in tasks:
            if task['telegram_user_id']:
                tasks_dict[task['telegram_user_id']].append(task)

        for user_id, tasks in tasks_dict.items():
            await bot.send_message(chat_id=user_id, text="Tasks available in tasklist:",
                                   reply_markup=task_keyboard(tasks))


async def check_for_camunda_tasks(dispatcher):
    while True:
        # Assume you have a list of user IDs to poll tasks for
        await fetch_camunda_task_and_send_notification()

        await asyncio.sleep(300)  # Check every 60 seconds, adjust as needed


async def on_startup() -> None:
    logger.info("bot starting...")

    register_middlewares(dp)

    dp.include_router(get_handlers_router())

    if settings.USE_WEBHOOK:
        app.middlewares.append(prometheus_middleware_factory())
        app.router.add_route("GET", "/metrics", MetricsView)

    await set_default_commands(bot)
    asyncio.create_task(check_for_camunda_tasks(dp))  # Start the polling task

    bot_info = await bot.get_me()

    logger.info(f"Name     - {bot_info.full_name}")
    logger.info(f"Username - @{bot_info.username}")
    logger.info(f"ID       - {bot_info.id}")

    states: dict[bool | None, str] = {
        True: "Enabled",
        False: "Disabled",
        None: "Unknown (This's not a bot)",
    }

    logger.info(f"Groups Mode  - {states[bot_info.can_join_groups]}")
    logger.info(f"Privacy Mode - {states[not bot_info.can_read_all_group_messages]}")
    logger.info(f"Inline Mode  - {states[bot_info.supports_inline_queries]}")

    logger.info("bot started")


async def on_shutdown() -> None:
    logger.info("bot stopping...")

    await remove_default_commands(bot)

    await dp.storage.close()
    await dp.fsm.storage.close()

    await bot.delete_webhook()
    await bot.session.close()

    logger.info("bot stopped")


async def setup_webhook() -> None:
    await bot.set_webhook(
        settings.webhook_url,
        allowed_updates=dp.resolve_used_update_types(),
        secret_token=settings.WEBHOOK_SECRET,
    )

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=settings.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.WEBHOOK_HOST, port=settings.WEBHOOK_PORT)
    await site.start()

    await asyncio.Event().wait()


class IsGroupFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]


class BotMentionFilter(BaseFilter):
    def __init__(self):
        self.bot_username = None

    async def get_bot_username(self):
        me = await bot.me()
        self.bot_username = me.username

    async def __call__(self, message: Message) -> bool:
        if not self.bot_username:
            await self.get_bot_username()
        return self.bot_username and f"@{self.bot_username}" in message.text


async def handle_mention_message(message: Message):
    chat_id = message.chat.id
    mention_data = {
        "message_id": message.message_id,
        "from_user": message.from_user.id,
        "text": message.text,
        "date": message.date.isoformat()
    }
    await message.answer("Mention saved!")


async def main() -> None:
    # if settings.SENTRY_DSN:
    #     sentry_loguru = LoguruIntegration(
    #         level=LoggingLevels.INFO.value,
    #         event_level=LoggingLevels.INFO.value,
    #     )
    #     sentry_sdk.init(
    #         dsn=settings.SENTRY_DSN,
    #         enable_tracing=True,
    #         traces_sample_rate=1.0,
    #         profiles_sample_rate=1.0,
    #         integrations=[sentry_loguru],
    #     )

    logger.add(
        "logs/telegram_bot.log",
        level="DEBUG",
        format="{time} | {level} | {module}:{function}:{line} | {message}",
        rotation="100 KB",
        compression="zip",
    )

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await bot.delete_webhook(drop_pending_updates=True)
    if settings.USE_WEBHOOK:
        await setup_webhook()
    else:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    uvloop.run(main())
