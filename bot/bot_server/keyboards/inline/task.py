from typing import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def task_keyboard(tasks: Sequence[dict]) -> InlineKeyboardMarkup:
    """Use in main menu."""

    buttons = []
    for task in tasks:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=task['name'],
                    callback_data=f'claim_task:{task["id"]}',
                )
            ]
        )

    keyboard = InlineKeyboardBuilder(markup=buttons)

    return keyboard.as_markup()
