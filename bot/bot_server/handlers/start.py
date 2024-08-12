import asyncio
import logging

import httpx
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery

from bot_server.core.config import settings
from bot_server.handlers.tasks import fetch_camunda_tasks
from bot_server.handlers.user_inputs import handle_upload_new, start_definition_by_key, \
    start_process_instance
from bot_server.keyboards.inline.task import task_keyboard
from bot_server.services.users import get_user
from camunda_client import CamundaEngineClient
from camunda_client.clients.dto import AuthData
from camunda_client.clients.engine.schemas import ProcessInstanceQuerySchema

router = Router()


class Form(StatesGroup):
    waiting_for_input = State()


@router.message(Command(commands=["start"]))
async def events_handler(message: types.Message, state: FSMContext) -> None:
    try:
        user_data = await state.get_data()
        user_info = user_data.get("user")
        await state.clear()
        await state.update_data(user=user_info)
        await state.update_data(resulting_variables=[{"name": "is_telegram",
                                                      "value": True,
                                                      "type": "Boolean"
                                                      }])
        camunda_user_id = user_info.get("camunda_user_id")
        camunda_key = user_info.get("camunda_key")
        business_key = user_info.get("id")
        async with httpx.AsyncHTTPTransport() as transport:
            camunda_client = CamundaEngineClient(
                auth_data=AuthData(username=camunda_user_id, password=camunda_key),
                base_url=settings.ENGINE_URL,
                transport=transport,
            )
            # Start the process instance with the collected variables
            process_instance = await camunda_client.get_process_instances(
                params=ProcessInstanceQuerySchema(
                    business_key=business_key,
                    process_definition_key="processUserSignUp"
                )
            )
            await camunda_client.close()
            if process_instance:
                process_instance = process_instance[0]
        if not process_instance:
            process_instance = await start_process_instance(state,
                                                            business_key=business_key,
                                                            process_definition_key="processUserSignUp",
                                                            camunda_user_id=user_info.get("camunda_user_id"),
                                                            camunda_key=user_info.get("camunda_key"))
        process_instance_id = process_instance.id
        if process_instance_id:
            await asyncio.sleep(2)
            tasks = await fetch_camunda_tasks(root_process_instance_id=process_instance_id,
                                              camunda_user_id=user_info.get("camunda_user_id"))
            if tasks:
                await message.bot.send_message(message.from_user.id,
                                               "Tasks available in tasklist:",
                                               reply_markup=task_keyboard(tasks))
            else:
                await message.bot.send_message(message.from_user.id,
                                               "No tasks available.")
        await message.bot.send_message(message.from_user.id, "User signed up. Run /generate to generate art.")
    except Exception as e:
        await state.clear()
        logging.error(f"Error starting generation: {e}")
        await message.answer(f"Error starting generation, {str(e)}")


@router.callback_query(F.data.startswith('upload_new'))
async def upload_new_callback(callback_query: types.CallbackQuery, state: FSMContext):
    _, index = callback_query.data.split(':')
    current_image_variable_index = int(index)
    await handle_upload_new(callback_query.from_user.id, state, callback_query.bot,
                            current_image_variable_index)


@router.callback_query(F.data.startswith('process_instance_started'))
async def process_instance_started_callback(callback_query: types.CallbackQuery, state: FSMContext):
    process_instance_id = callback_query.data.split(":")[1]
    user_data = await state.get_data()
    user_info = user_data.get("user")
    await state.clear()
    await state.update_data(user=user_info)
    if process_instance_id:
        await asyncio.sleep(2)
        tasks = await fetch_camunda_tasks(root_process_instance_id=process_instance_id,
                                          camunda_user_id=user_info.get("camunda_user_id"))
        if tasks:
            await callback_query.bot.send_message(callback_query.from_user.id,
                                                  "Tasks available in tasklist:",
                                                  reply_markup=task_keyboard(tasks))
        else:
            await callback_query.bot.send_message(callback_query.from_user.id,
                                                  "No tasks available.")


@router.callback_query(F.data.startswith('start_definition'))
async def start_definition_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    user_info = user_data.get("user")
    process_definition_key = callback_query.data.split(":")[1]
    await start_definition_by_key(
        callback_query.bot, state,
        process_definition_key=process_definition_key,
        camunda_user_id=user_info.get("camunda_key"),
        camunda_key=user_info.get("camunda_key"),
    )


@router.callback_query(F.data.startswith('start_process_instance'))
async def start_process_instance_from_def_by_key(callback_query: CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        user_info = user_data.get("user")
        if not user_info:
            user_info_obj = await get_user(state.key.user_id)
            camunda_user_id = user_info_obj.camunda_user_id
            camunda_key = user_info_obj.camunda_key
        else:
            camunda_user_id = user_info.get("camunda_user_id")
            camunda_key = user_info.get("camunda_key")
        process_definition_key = callback_query.data.split(":")[1]
        process_instance = await start_process_instance(
            state,
            process_definition_key,
            camunda_user_id=camunda_user_id,
            camunda_key=camunda_key
        )
        await callback_query.bot.send_message(callback_query.from_user.id,
                                              f"Process instance started: {process_instance.id}")
        await asyncio.sleep(2)
        tasks = await fetch_camunda_tasks()
        if tasks:
            await callback_query.bot.send_message(callback_query.from_user.id,
                                                  "Tasks available in tasklist:",
                                                  reply_markup=task_keyboard(tasks))
    except Exception as e:
        await state.clear()
        logging.error(f"Error starting process instance: {e}")
        await callback_query.bot.send_message(callback_query.from_user.id,
                                              "Error starting process instance, re-initiate the form")


@router.callback_query(F.data.startswith('edit_variable'))
async def edit_variable_callback(callback_query: CallbackQuery, state: FSMContext):
    from bot_server.handlers.user_inputs import edit_variable
    await edit_variable(callback_query, state, Form)


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


@router.callback_query(F.data.startswith('generate_qr_code'))
async def generate_qr_code_callback(callback_query: CallbackQuery, state: FSMContext):
    from bot_server.handlers.user_inputs import generate_qr_code
    from bot_server.handlers.tasks import complete_task_callback
    try:
        await generate_qr_code(callback_query, state)
        await complete_task_callback(callback_query, state)
    except Exception as e:
        await callback_query.answer(f"Failed to generate QR code: {str(e)[:100]}")
