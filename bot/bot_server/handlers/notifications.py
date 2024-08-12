from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.i18n import gettext as _

from bot_server.keyboards.inline.contacts import contacts_keyboard

router = Router(name="notifications")


@router.message(Command(commands=["notifications"]))
async def notifications_handler(message: types.Message) -> None:
    """Return a button with a link to the project."""
    await message.answer(_("Not Implemented yet, Reach for support https://t.me/evahteev"), reply_markup=contacts_keyboard())
