import asyncio

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot_server.filters.users import UserContextFilter
from bot_server.handlers.tasks import fetch_camunda_tasks
from bot_server.handlers.user_inputs import get_process_definitions, handle_upload_new, start_definition_by_key
from bot_server.keyboards.inline.start_process import start_process_keyboard
from bot_server.keyboards.inline.task import task_keyboard

router = Router()


class Form(StatesGroup):
    waiting_for_input = State()


@router.message(Command(commands=["accounts", "account", "user"]))
async def artworks_handler(message: types.Message, state: FSMContext) -> None:
    process_definitions = await get_process_definitions(prefix="accounts")
    await state.clear()
    # Assuming main_keyboard is implemented elsewhere
    await message.answer("Artwork actions:", reply_markup=start_process_keyboard(process_definitions))


@router.callback_query(F.data.startswith('upload_new'))
async def upload_new_callback(callback_query: types.CallbackQuery, state: FSMContext):
    _, index = callback_query.data.split(':')
    current_image_variable_index = int(index)
    await handle_upload_new(callback_query.from_user.id, state, callback_query.bot,
                            current_image_variable_index)


@router.callback_query(F.data.startswith('process_instance_started'))
async def process_instance_started_callback(callback_query: types.CallbackQuery, state: FSMContext):
    process_instance_id = callback_query.data.split(":")[1]
    if process_instance_id:
        await asyncio.sleep(2)
        tasks = await fetch_camunda_tasks(user_id=callback_query.from_user.id,
                                          process_instance_id=process_instance_id)
        if tasks:
            await callback_query.bot.send_message(callback_query.from_user.id,
                                                  "Tasks available in tasklist:",
                                                  reply_markup=task_keyboard(tasks))
        else:
            await callback_query.bot.send_message(callback_query.from_user.id,
                                                  "No tasks available.")


@router.callback_query(F.data.startswith('start_definition'), UserContextFilter())
async def start_definition_callback(callback_query: types.CallbackQuery, state: FSMContext, session:AsyncSession):
    user_data = await state.get_data()
    user_info = user_data.get("user")

    process_definition_key = callback_query.data.split(":")[1]

    await start_definition_by_key(
        callback_query.from_user.id,
        callback_query.bot, state,
        process_definition_key,
        session,
        camunda_user_id=user_info.get("camunda_user_id"),
        camunda_key=user_info.get("camunda_key"),
    )

@router.callback_query(F.data.startswith('claim_task'))
async def claim_task_callback(callback_query: CallbackQuery, state: FSMContext):
    from bot_server.handlers.user_inputs import claim_task
    await claim_task(callback_query, state)


@router.callback_query(F.data.startswith('set_variable'))
async def set_variable_callback(callback_query: CallbackQuery, state: FSMContext):
    from bot_server.handlers.user_inputs import set_variable
    await set_variable(callback_query, state, Form)


# @router.message(Form.waiting_for_input)
# async def _process_input(message: types.Message, state: FSMContext):
#     from bot_server.handlers.user_inputs import process_input
#     await process_input(message, state, Form)
