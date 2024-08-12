import asyncio
from typing import Sequence
from uuid import UUID

import httpx
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery

from bot_server.core.config import settings
from bot_server.keyboards.inline.task import task_keyboard
from bot_server.services.users import get_user_by_camunda_user_id, get_user
from camunda_client import VariableValueSchema
from camunda_client.clients.dto import AuthData
from camunda_client.clients.engine.client import CamundaEngineClient
from camunda_client.clients.engine.schemas import GetHistoryTasksFilterSchema

router = Router()


class Form(StatesGroup):
    waiting_for_input = State()


async def fetch_camunda_tasks(camunda_user_id: str | None = None,
                              root_process_instance_id: UUID | None = None) -> Sequence[dict]:
    async with (httpx.AsyncHTTPTransport() as transport):

        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=settings.ENGINE_USERNAME, password=settings.ENGINE_PASSWORD),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        tasks = await camunda_client.get_history_tasks(schema=GetHistoryTasksFilterSchema(unfinished=True))
        tasks_to_ping = []

        for task in tasks:
            if root_process_instance_id:
                if str(task.root_process_instance_id) != str(root_process_instance_id):
                    continue
            if camunda_user_id:
                if task.assignee != str(camunda_user_id):
                    continue
            user = await get_user_by_camunda_user_id(task.assignee)
            variables = await camunda_client.get_variable_instances(
                process_instance_id=task.process_instance_id)
            tasks_to_ping.append({"task": task,
                                  "id": task.id,
                                  "name": task.name,
                                  "telegram_user_id": user.telegram_user_id if user else None,
                                  "variables": variables
                                  })
        await camunda_client.close()
        return tasks_to_ping


@router.message(Command(commands=["tasks", "inbox"]))
async def tasks_handler(message: types.Message, state: FSMContext) -> None:
    """Information about bot_server."""
    user_data = await state.get_data()
    user_info = user_data.get("user")
    await state.clear()
    await state.update_data(user=user_info)
    tasks = await fetch_camunda_tasks()
    if not tasks:
        await message.answer("No tasks available.")
    else:
        await message.answer("Tasks available in tasklist:", reply_markup=task_keyboard(tasks))


async def get_task_form_variables(task_id: str, state: FSMContext):
    user_data = await state.get_data()
    user_info = user_data.get("user")
    if not user_info:
        user_info_obj = await get_user(state.key.user_id)
        camunda_user_id = user_info_obj.camunda_user_id
        camunda_key = user_info_obj.camunda_key
        await state.update_data(user=user_info_obj.to_dict())
    else:
        camunda_user_id = user_info.get("camunda_user_id")
        camunda_key = user_info.get("camunda_key")
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        variables = await camunda_client.get_task_form_variables(task_id)
        return variables


async def get_task(task_id: str, state: FSMContext):
    user_data = await state.get_data()
    user_info = user_data.get("user")
    if not user_info:
        user_info_obj = await get_user(state.key.user_id)
        camunda_user_id = user_info_obj.camunda_user_id
        camunda_key = user_info_obj.camunda_key
    else:
        camunda_user_id = user_info.get("camunda_user_id")
        camunda_key = user_info.get("camunda_key")

    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        task_info = await camunda_client.get_task(task_id)
        return task_info


async def complete_task(state: FSMContext, task_id: str,
                        camunda_user_id: str = settings.ENGINE_USERNAME, camunda_key: str = settings.ENGINE_PASSWORD):
    data = await state.get_data()
    variables = data['resulting_variables']
    # Convert variables to Camunda's expected format
    camunda_variables = {var['name']: {'value': var['value'], 'type': var['type']} for var in variables}
    variables = camunda_variables
    variables_fixed = {}
    for key, value in variables.items():
        value = VariableValueSchema(**value)
        variables_fixed[key] = value
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        # Start the process instance with the collected variables
        return await camunda_client.complete_task(task_id=task_id,
                                                  variables=variables_fixed)

async def get_history_task(task_id: str):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=settings.ENGINE_USERNAME, password=settings.ENGINE_PASSWORD),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        # Start the process instance with the collected variables
        return await camunda_client.get_history_tasks(schema=GetHistoryTasksFilterSchema(task_id=task_id))


@router.callback_query(F.data.startswith('complete_task'))
async def complete_task_callback(callback_query: CallbackQuery, state: FSMContext):
    _, task_id = callback_query.data.split(':')
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

        await complete_task(state, task_id, camunda_user_id, camunda_key)
    except Exception as e:
        await callback_query.answer(f"Failed to complete task: {str(e)[:100]}")
        return
    await callback_query.answer("Task completed")
    await asyncio.sleep(2)
    history_tasks = await get_history_task(task_id)
    if not history_tasks:

        tasks = await fetch_camunda_tasks(camunda_user_id=user_info.get("camunda_user_id"))
    else:
        tasks = await fetch_camunda_tasks(root_process_instance_id=history_tasks[0].root_process_instance_id,
                                      camunda_user_id=history_tasks[0].assignee)
    if tasks:
        await callback_query.bot.send_message(callback_query.from_user.id,
                                              "Tasks available in tasklist:",
                                              reply_markup=task_keyboard(tasks))
    else:
        await callback_query.bot.send_message(callback_query.from_user.id,
                                              "No tasks available.")


@router.callback_query(F.data.startswith('claim_task'))
async def claim_task_callback(callback_query: CallbackQuery, state: FSMContext):
    from bot_server.handlers.user_inputs import claim_task
    user_data = await state.get_data()
    user_info = user_data.get("user")
    await state.clear()
    await state.update_data(user=user_info)
    await claim_task(callback_query, state)


@router.callback_query(F.data.startswith('set_variable'))
async def set_variable_callback(callback_query: CallbackQuery, state: FSMContext):
    from bot_server.handlers.user_inputs import set_variable
    await set_variable(callback_query, state, Form)


@router.message(Form.waiting_for_input)
async def _process_input(message: types.Message, state: FSMContext):
    from bot_server.handlers.user_inputs import process_input
    await process_input(message, state, Form)


@router.callback_query(F.data.startswith('generate_qr_code'))
async def generate_qr_code_callback(callback_query: CallbackQuery, state: FSMContext):
    from bot_server.handlers.user_inputs import generate_qr_code
    try:
        await generate_qr_code(callback_query, state)
        await complete_task_callback(callback_query, state)
    except Exception as e:
        await callback_query.answer(f"Failed to generate QR code: {str(e)[:100]}")
