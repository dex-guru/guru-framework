from typing import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from camunda_client.clients.engine.schemas import ProcessDefinitionSchema


def start_process_keyboard(process_definitions: Sequence[ProcessDefinitionSchema]) -> InlineKeyboardMarkup:
    """Use in artworks menu."""

    buttons = []
    for process_definition in process_definitions:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=process_definition.name,
                    callback_data=f'start_definition:{process_definition.key}',
                )
            ]
        )

    keyboard = InlineKeyboardBuilder(markup=buttons)

    # keyboard.adjust(1, 1, 2)

    return keyboard.as_markup()
