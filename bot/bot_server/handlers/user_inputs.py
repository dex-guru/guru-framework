import asyncio
import io
import logging
import uuid
from io import BytesIO
from urllib.parse import urlparse, parse_qs, urlencode

import boto3
import httpx
from PIL import Image
from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from botocore.exceptions import NoCredentialsError
from pyzbar.pyzbar import decode
from sqlalchemy.ext.asyncio import AsyncSession

from bot_server.core.config import settings
from bot_server.handlers.tasks import get_task_form_variables, get_task, fetch_camunda_tasks
from bot_server.keyboards.inline.task import task_keyboard
from camunda_client.clients.dto import AuthData
from camunda_client.clients.engine.client import CamundaEngineClient
from camunda_client.clients.engine.schemas import ProcessInstanceSchema
from flow_client import FlowClient


async def download_telegram_photo(bot: Bot, photo: types.PhotoSize) -> bytes:
    """
    Downloads a photo from Telegram servers.

    Parameters:
    - bot: Instance of your aiogram Bot.
    - photo: PhotoSize object representing the photo to be downloaded.

    Returns:
    - The binary content of the photo.
    """
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    download_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"

    async with httpx.AsyncClient() as client:
        response = await client.get(download_url)
        response.raise_for_status()  # Raises an exception for HTTP errors
        return response.content


def upload_file_to_s3_binary(content: bytes, bucket_name, s3_file_name) -> str:
    """
    Uploads binary content to AWS S3 and returns the file URL.

    Parameters:
    - content: Binary content of the file to upload.
    - bucket_name: Name of the S3 bucket.
    - s3_file_name: Object name in S3.

    Returns:
    - URL of the uploaded file on success.
    """
    s3 = boto3.client('s3',
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                      region_name=settings.AWS_REGION_NAME)
    try:
        s3.put_object(Bucket=bucket_name, Key=s3_file_name, Body=content)
        location = s3.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
        url = f"https://{bucket_name}.s3.{location}.amazonaws.com/{s3_file_name}"
        return url
    except NoCredentialsError:
        print("Credentials not available")
        return None


def parse_url_query(url):
    # Parse the URL
    parsed_url = urlparse(url)
    # Extract the query string
    query_string = parsed_url.query
    # Parse the query string into a dictionary
    # parse_qs returns a dictionary where values are list of values for each key.
    # Use dict comprehension to convert lists to single values if you need.
    query_params = parse_qs(query_string)
    # Convert lists to individual values if necessary
    query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
    return query_params


async def process_image_upload(message: types.Message, state: FSMContext, form):
    data = await state.get_data()
    variables = data.get("variables")
    callback_name = data.get("callback_name")
    index = 0
    if not callback_name or not variables:
        raise ValueError("Form type/variables are not set in the state data.")
    if data.get("image_upload"):
        # Assume user uploaded an image for the current variable
        photo = message.photo[-1]  # Get the highest quality photo
        # Here you would upload the photo to an S3 bucket and get the URL, for now, let's pretend we have a URL
        # Download the photo
        photo_bytes = await download_telegram_photo(message.bot, photo)

        # Generate a unique name for the S3 object, e.g., using UUID
        s3_file_name = f"images/{uuid.uuid4()}.jpg"

        # Upload to S3
        photo_url = upload_file_to_s3_binary(photo_bytes, settings.AWS_S3_BUCKET, s3_file_name)

        # Save the image URL as the variable value
        index = data["current_image_variable_index"]
        variables = data["variables"]
        resulting_variables = data.get("resulting_variables", [])

        resulting_variables.append({
            "name": variables[index]['name'],
            "value": photo_url,
            "type": variables[index]['value']['type']
        })

        # Update state to indicate the image has been processed and move to the next variable
        await state.update_data(awaiting_image=False, resulting_variables=resulting_variables)
    elif data.get("image_qr"):
        # as we are not saving QR image into variables anyhow, index = -1
        index = -1
        # Assume user uploaded a QR code image
        photo = message.photo[-1]
        photo_bytes = await download_telegram_photo(message.bot, photo)
        # Process the QR code image
        image = Image.open(BytesIO(photo_bytes))

        # Step 3: Use pyzbar to decode the QR code from the image
        decoded_objects = decode(image)

        if decoded_objects:
            # Assuming there is at least one QR code
            qr_data = decoded_objects[0].data.decode('utf-8')
            await message.bot.send_message(message.from_user.id, f"QR Code data: {qr_data}")
        else:
            qr_data = None
            await message.bot.send_message(message.from_user.id, "No QR Code found")
        # Update state to indicate the image has been processed
        parsed_url = urlparse(qr_data)

        # Extract and convert the query parameters into a dictionary
        query_params = parse_qs(parsed_url.query)

        resulting_variables = data.get("resulting_variables", [])

        for key, value in query_params.items():
            resulting_variables.append({
                "name": key,
                "value": value,
                "type": "String"
            })

        await state.update_data(awaiting_image=False, image_qr=False, resulting_variables=resulting_variables)
    else:
        # If not expecting an image, you could remind the user to follow the instructions or handle as needed
        await message.reply("Currently not expecting an image. Please follow the instructions provided.")
        await state.update_data(awaiting_image=False, image_qr=False)
    if data.get("callback_name") and data.get("form_key"):
        callback_name = data["callback_name"]
        form_key = data["form_key"]
        keyboard = InlineKeyboardBuilder(markup=[
            [InlineKeyboardButton(text=f"{callback_name}",
                                  callback_data=f"{callback_name}:{form_key}")]])
        if index >= 0:
            await message.bot.send_message(message.from_user.id,
                                           f"Accepted: {variables[index]['name']}",
                                           reply_markup=keyboard.as_markup())
        else:
            await message.bot.send_message(message.from_user.id, f"Accepted QR Code data",
                                           reply_markup=keyboard.as_markup())


async def handle_upload_new(chat_id, state: FSMContext, bot: Bot,
                            current_image_variable_index: int):
    # Prompt user to upload a new image
    await bot.send_message(chat_id, "Please upload the new image.")
    await state.update_data(awaiting_image=True, image_upload=True,
                            current_image_variable_index=current_image_variable_index)


async def handle_upload_qr(chat_id, state: FSMContext, bot: Bot):
    # Prompt user to upload a new image
    await bot.send_message(chat_id, "Please scan/upload QR Code.")
    await state.update_data(awaiting_image=True, image_qr=True)


async def start_process_instance(state: FSMContext,
                                 process_definition_key: str | None = None,
                                 business_key: str | None = None,
                                 camunda_user_id: str = settings.ENGINE_USERNAME,
                                 camunda_key: str = settings.ENGINE_PASSWORD) -> ProcessInstanceSchema:
    data = await state.get_data()
    process_definition_key = data['process_definition_key'] if not process_definition_key else process_definition_key
    variables = data.get('resulting_variables', [])
    camunda_variables = {var['name']: {'value': var['value'], 'type': var['type']} for var in variables}
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        # Start the process instance with the collected variables
        process_instance = await camunda_client.start_process(process_definition_key,
                                                              business_key=business_key,
                                                              variables=camunda_variables)
        await camunda_client.close()
    return process_instance


async def process_input(message: types.Message, state: FSMContext, form):
    try:
        data = await state.get_data()
        variables = data.get("variables")
        callback_name = data.get("callback_name")
        if not callback_name or not variables:
            raise ValueError("Form type/variables are not set in the state data.")
        if data.get("awaiting_image"):
            await process_image_upload(message, state, form)
            data = await state.get_data()
            resulting_variables = data.get("resulting_variables", [])
            index = data["current_image_variable_index"]
        else:
            resulting_variables = data.get("resulting_variables", [])
            index = data["current_index"]
            user_input = message.text

            resulting_variables.append({
                "name": variables[index]['name'],
                "value": user_input,
                "type": variables[index]['value']['type']
            })

        await state.update_data(resulting_variables=resulting_variables)

        if data.get("callback_name") and data.get("form_key") and len(variables) >= index:
            callback_name = data["callback_name"]
            form_key = data["form_key"]
            keyboard = InlineKeyboardBuilder(markup=[
                [InlineKeyboardButton(text=f"{callback_name}",
                                      callback_data=f"{callback_name}:{form_key}")]])
            await message.bot.send_message(message.from_user.id,
                                           f"Accepted: {variables[index]['name']}: {user_input}",
                                           reply_markup=keyboard.as_markup())

    except Exception as e:
        logging.error(f"Unexpected input error: {e}")


async def edit_variable(callback_query: CallbackQuery, state: FSMContext, form):
    await callback_query.answer()  # Optional: Provides immediate feedback to the user
    # Extract the index of the variable from the callback data
    _, index = callback_query.data.split(':')
    index = int(index)
    data = await state.get_data()
    variables = data.get("variables")
    await callback_query.bot.send_message(callback_query.from_user.id, f"Enter {variables[index]['name']}")
    await state.update_data(current_index=index)
    await state.set_state(form.waiting_for_input)


async def set_variable(callback_query: CallbackQuery, state: FSMContext, form):
    await callback_query.answer()  # Optional: Provides immediate feedback to the user

    # Extract the index of the variable from the callback data
    _, index, value = callback_query.data.split(':')
    index = int(index)

    data = await state.get_data()
    variables = data.get("variables")
    resulting_variables = data.get("resulting_variables", [])
    callback_name = data.get("callback_name")
    if not callback_name or not variables:
        raise ValueError("Form type/variables are not set in the state data.")
    resulting_variables[index] = {
        "name": variables[index]['name'],
        "value": value,
        "type": variables[index]['value']['type']
    }
    await state.update_data(resulting_variables=resulting_variables)


async def get_process_definition_start_form_variables(process_definition_key: str,
                                                      camunda_user_id: str = settings.ENGINE_USERNAME,
                                                      camunda_key: str = settings.ENGINE_PASSWORD):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        variables = await camunda_client.get_process_definition_start_form(process_definition_key)
        return variables


async def generate_qr_code(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    task_id = callback_query.data.split(":")[1]
    task_variables = await get_task_form_variables(task_id, state, session)
    task_variables_list = []
    task_variables_dict = {}

    for variable in task_variables:
        task_variables_list.append(
            variable.model_dump()
        )
        task_variables_dict[variable.name] = variable.model_dump()

    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    # b'https://pixelpact.ai/?event_id=1&art_id=1'
    params = urlencode({key: value['value']['value'] for key, value in task_variables_dict.items()})
    qr_data = (f"{settings.SERVICE_URL}/?{params}")
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Assuming `img` is your PIL Image object
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")  # Or PNG, depending on your requirements
    image_bytes = buffer.getvalue()

    s3_file_name = f"qr/{uuid.uuid4()}.jpg"
    # Upload to S3
    photo_url = upload_file_to_s3_binary(image_bytes, settings.AWS_S3_BUCKET, s3_file_name)

    # Send QR code as photo
    await callback_query.bot.send_photo(chat_id=callback_query.from_user.id, photo=photo_url)

async def compose_review_keyboard(bot: Bot, user_id: int, start_form_variables: list,
                                callback_name: str, form_key: str):
    buttons = []
    for idx, variable in enumerate(start_form_variables):
        variable_name = variable['name']
        if variable_name == "is_regenerate":
            buttons.append([
                InlineKeyboardButton(
                    text="Regenerate?",
                    callback_data=f"set_variable:{idx}:{True}",
                )
            ])
            continue
    keyboard = InlineKeyboardBuilder(markup=buttons)
    await bot.send_message(user_id, "Regenerate or Complete?", reply_markup=keyboard.as_markup())
    keyboard = InlineKeyboardBuilder(markup=[
        [InlineKeyboardButton(text=f"{callback_name}",
                              callback_data=f"{callback_name}:{form_key}")]])
    await bot.send_message(user_id, "Complete", reply_markup=keyboard.as_markup())

async def compose_form_keyboard(bot: Bot, user_id: int, start_form_variables: list,
                                callback_name: str, form_key: str):
    buttons = []
    for idx, variable in enumerate(start_form_variables):
        variable_type = variable['value']['type']
        variable_name = variable['name']
        variable_value = variable['value'].get('value')
        if variable_type == 'String' and 'img_' in variable_name:
            if variable_value:
                buttons.append([InlineKeyboardButton(text=f"Default {variable_name}",
                                                     callback_data=f"set_variable:{idx}:{True}"),
                                InlineKeyboardButton(text="Upload new image", callback_data=f"upload_new:{idx}")])
            else:
                buttons.append([InlineKeyboardButton(text=f"Upload new {variable_name}",
                                                     callback_data=f"upload_new:{idx}")])
            continue
        if variable_type == 'Boolean':
            true_text = f"{variable_name}: True"
            false_text = f"{variable_name}: False"
            if variable_value:
                true_text += "(Default)"
            else:
                false_text += "(Default)"
            buttons.append([
                InlineKeyboardButton(text=true_text, callback_data=f"set_variable:{idx}:{True}"),
                InlineKeyboardButton(text=false_text, callback_data=f"set_variable:{idx}:{False}")])
            continue
        if not variable_value:
            buttons.append([InlineKeyboardButton(text=f"Edit {variable_name}:{variable_type}",
                                                 callback_data=f"edit_variable:{idx}")])
        else:
            buttons.append(
                [InlineKeyboardButton(text=f"Edit {variable_name}:{variable_type}, default: {variable_value}",
                                      callback_data=f"edit_variable:{idx}")])
    keyboard = InlineKeyboardBuilder(markup=buttons)
    await bot.send_message(user_id, "Please fill in the form:", reply_markup=keyboard.as_markup())
    keyboard = InlineKeyboardBuilder(markup=[
        [InlineKeyboardButton(text=f"{callback_name}",
                              callback_data=f"{callback_name}:{form_key}")]])
    await bot.send_message(user_id, f"Actions after: {callback_name}:{form_key}", reply_markup=keyboard.as_markup())


async def get_process_definitions(prefix: str | None = None, camunda_user_id: str = settings.ENGINE_USERNAME,
                                  camunda_key: str = settings.ENGINE_PASSWORD):
    async with httpx.AsyncHTTPTransport() as transport:
        camunda_client = CamundaEngineClient(
            auth_data=AuthData(username=camunda_user_id, password=camunda_key),
            base_url=settings.ENGINE_URL,
            transport=transport,
        )
        process_definitions = await camunda_client.get_process_definitions()
        process_definitions_artwork = {}
        for process_definition in process_definitions:
            if prefix and process_definition.key.startswith(prefix):
                process_definitions_artwork[process_definition.name] = process_definition
            elif not prefix:
                process_definitions_artwork[process_definition.name] = process_definition
        return list(process_definitions_artwork.values())


async def start_definition_by_key(user_id,
                                  bot: Bot,
                                  state: FSMContext,
                                  process_definition_key: str,
                                  camunda_user_id: str = settings.ENGINE_USERNAME,
                                  camunda_key: str = settings.ENGINE_PASSWORD):
    start_form_variables = await get_process_definition_start_form_variables(process_definition_key,
                                                                             camunda_user_id=camunda_user_id,
                                                                             camunda_key=camunda_key)
    # Assuming model_dump converts the variables to a list of dicts
    start_form_variables = [variable.model_dump() for variable in start_form_variables]
    data = await state.get_data()
    resulting_variables = data.get("resulting_variables", [])
    for variable in start_form_variables:
        resulting_variables.append({
            "name": variable['name'],
            "value": variable['value']['value'],
            "type": variable['value']['type']
        })
    await state.update_data(**{"variables": start_form_variables, "current_index": 0,
                               "callback_name": "start_process_instance",
                               "form_key": process_definition_key,
                               "resulting_variables": resulting_variables})
    await state.update_data(process_definition_key=process_definition_key)
    if start_form_variables:
        await compose_form_keyboard(bot, user_id, start_form_variables,
                                    callback_name="start_process_instance", form_key=process_definition_key)
    else:
        process_instance = await start_process_instance(state, process_definition_key, camunda_user_id, camunda_key)
        await bot.send_message(user_id, f"Process instance started: {process_instance.id}")
        await asyncio.sleep(2)
        tasks = await fetch_camunda_tasks(camunda_user_id=camunda_user_id,
                                          root_process_instance_id=process_instance.id)
        if tasks:
            await bot.send_message(user_id,
                                   "Tasks available in tasklist:",
                                   reply_markup=task_keyboard(tasks))


async def claim_task(callback_query: CallbackQuery, state: FSMContext):
    task_id = callback_query.data.split(":")[1]
    task_info = await get_task(task_id, state)
    task_variables = await get_task_form_variables(task_id, state)
    task_variables_list = []
    task_variables_dict = {}

    for variable in task_variables:
        task_variables_list.append(
            variable.model_dump()
        )
        task_variables_dict[variable.name] = variable.model_dump()

    user_data = await state.get_data()
    user_info = user_data.get("user")

    if task_info.assignee == user_info.get("camunda_user_id"):
        if task_info.task_definition_key == "qr_reading":
            # Send QR code as photo
            await handle_upload_qr(callback_query.from_user.id, state, callback_query.bot)
            state_data = await state.get_data()
            qr_data = state_data.get("qr_data")
            await callback_query.bot.send_message(callback_query.from_user.id, f"QR Code data: {qr_data}")

    data = await state.get_data()
    resulting_variables = data.get("resulting_variables", [])
    resulting_variables_dict = {var['name']: var for var in resulting_variables}

    for variable in task_variables_list:
        name = variable['name']
        value = variable['value']['value']
        var_type = variable['value']['type']
        if var_type == 'Boolean':
            value = bool(value)
        if name in resulting_variables_dict:
            # Update the existing variable
            resulting_variables_dict[name]['value'] = value
            resulting_variables_dict[name]['type'] = var_type
        else:
            # Append the new variable
            resulting_variables_dict[name] = {
                "name": name,
                "value": value,
                "type": var_type
            }
    resulting_variables = list(resulting_variables_dict.values())

    callback_name = "generate_qr_code" if task_info.task_definition_key == "generate_qr_code" else "complete_task"
    form_key = str(task_info.id)
    await state.update_data(**{"variables": task_variables_list, "current_index": 0,
                               "resulting_variables": resulting_variables,
                               "callback_name": callback_name, "form_key": form_key})
    if task_info.task_definition_key in ["review_modal_season_pass_invite"]:
        for variable in resulting_variables:
            if variable['name'] == "gen_art_id":
                async with FlowClient(base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY) as flow_client:
                    art = await flow_client.get_art_by_id(art_id=variable['value'])
                await callback_query.bot.send_photo(chat_id=callback_query.from_user.id, photo=art.img_picture)
                await compose_review_keyboard(callback_query.bot, callback_query.from_user.id, task_variables_list,
                                    callback_name, form_key)
                return
    if task_info.task_definition_key not in ["qr_reading"]:
        await compose_form_keyboard(callback_query.bot, callback_query.from_user.id, task_variables_list,
                                    callback_name, form_key)
