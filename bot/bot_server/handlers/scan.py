from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from urllib.parse import urlparse, parse_qs

from aiogram.fsm.state import StatesGroup, State

from bot_server.handlers.user_inputs import process_image_upload, start_definition_by_key, handle_upload_new, handle_upload_qr

router = Router(name="scan")

class Form(StatesGroup):
    waiting_for_input = State()


@router.message(Command(commands=["scan", "scan_qr"]))
async def scan_handler(message: types.Message, state: FSMContext) -> None:
    """Information about bot_server."""
    await state.clear()
    await state.update_data(image_qr=True)
    await handle_upload_qr(message.from_user.id, state, message.bot)


@router.message(F.photo)
async def process_artwork_image_upload(message: types.Message, state: FSMContext):
    await process_image_upload(message, state, Form)
