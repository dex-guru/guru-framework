from __future__ import annotations
from typing import TYPE_CHECKING

from aiogram.types import BotCommand, BotCommandScopeDefault

if TYPE_CHECKING:
    from aiogram import Bot

"""
        help - help
        account - manage account to access personalized features and settings
        events - view edit and delete events from their account
        artworks - Artworks Management
        scan - Scan QR code
        notifications - notifications for upcoming events reminders and updates
        tasks - tasklist management
        info - application info
        generate - generate t-shirt designs from their uploaded artwork and preview them before purchase
        stats - past orders sales statistics for vendors track shipments and access order details
        support - support contacts
"""


users_commands: dict[str, dict[str, str]] = {
    "en": {
        "start": "Start the bot",
        "generate": "Generate Meme",
        # "help": "help",
        # "automations": "Web3 Automations",
        # "strategy": "DeFi Strategies",
        # "running": "Running automations",
        # "info": "Service info",
        # "notifications": "notifications for upcoming events, reminders, and updates",
        # "tasks": "tasklist management",
        # "stats": "Automation Statistics",
        # "info": "application info",
        # "generate": "generate t-shirt designs from their uploaded artwork and preview them before purchase",
        # "support": "support contacts",
    },
    "uk": {
        "start": "Start the bot",
        "generate": "Generate Meme",
        # "help": "help",
        # "automations": "Web3 Automations",
        # "strategy": "DeFi Strategies",
        # "running": "Running automations",
        # "info": "Service info",
        # "notifications": "notifications for upcoming events, reminders, and updates",
        # "tasks": "tasklist management",
        # "stats": "Automation Statistics",
        # # "notifications": "notifications for upcoming events, reminders, and updates",
        # "tasks": "tasklist management",
        # "info": "application info",
        # "generate": "generate t-shirt designs from their uploaded artwork and preview them before purchase",
        # "stats": "past orders, sales statistics for vendors, track shipments, and access order details",
        # "support": "support contacts",
    },
}

admins_commands: dict[str, dict[str, str]] = {
    **users_commands,
    "en": {
        "ping": "Check bot ping",
        "stats": "Show bot stats",
    },
    "uk": {
        "ping": "Check bot ping",
        "stats": "Show bot stats",
    },
    "ru": {
        "ping": "Check bot ping",
        "stats": "Show bot stats",
    },
}


async def set_default_commands(bot: Bot) -> None:
    await remove_default_commands(bot)

    for language_code in users_commands:
        await bot.set_my_commands(
            [
                BotCommand(command=command, description=description)
                for command, description in users_commands[language_code].items()
            ],
            scope=BotCommandScopeDefault(),
        )

        """ Commands for admins
        for admin_id in await admin_ids():
            await bot.set_my_commands(
                [
                    BotCommand(command=command, description=description)
                    for command, description in admins_commands[language_code].items()
                ],
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        """


async def remove_default_commands(bot: Bot) -> None:
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
