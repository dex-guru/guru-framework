from __future__ import annotations

from typing import TYPE_CHECKING

from bot_server.cache.redis import build_key, cached, clear_cache
from bot_server.core.config import settings
from bot_server.models.user import UserModel


from flow_client import FlowClient
from flow_client.clients.flow.schemas import UserSchema

if TYPE_CHECKING:
    from aiogram.types import User

async def add_user(
    user: User,
    referrer: str | None,
) -> UserSchema:
    """Add a new user to the database."""
    user_id: int = user.id
    first_name: str = user.first_name
    last_name: str | None = user.last_name
    username: str | None = user.username
    language_code: str | None = user.language_code
    is_premium: bool = user.is_premium or False

    async with FlowClient(base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY) as flow_client:
        response = await flow_client.add_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_admin=False,
            is_suspicious=False,
            telegram_user_id=user_id,
            webapp_user_id=None,
            is_block=False,
            is_premium=is_premium,
        )
    await clear_cache(user_exists, user_id)
    return response


@cached(key_builder=lambda user_id: build_key(user_id))
async def user_exists(user_id: int) -> bool:
    """Checks if the user is in the database."""
    async with FlowClient(base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY) as flow_client:
        user = await flow_client.get_user(telegram_user_id=user_id)
    return bool(user)


@cached(key_builder=lambda user_id: build_key(user_id))
async def get_first_name(user_id: int) -> str:
    async with FlowClient(base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY) as flow_client:
        user = await flow_client.get_user(telegram_user_id=user_id)
    return user.first_name


@cached(key_builder=lambda user_id: build_key(user_id))
async def get_language_code(user_id: int) -> str:
    async with FlowClient(base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY) as flow_client:
        user = await flow_client.get_user(telegram_user_id=user_id)
    return user.language_code


async def set_language_code(
    user_id: int,
    language_code: str,
) -> None:
    async with FlowClient(base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY) as flow_client:
        user = await flow_client.get_user(telegram_user_id=user_id)
        user.language_code = language_code
        await flow_client.update_user(user)


@cached(key_builder=lambda user_id: build_key(user_id))
async def is_admin(user_id: int) -> bool:
    async with FlowClient(base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY) as flow_client:
        user = await flow_client.get_user(telegram_user_id=user_id)
    return bool(user.is_admin)


async def set_is_admin(user_id: int, is_admin: bool) -> None:
    async with FlowClient(base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY) as flow_client:
        user = await flow_client.get_user(telegram_user_id=user_id)
        user.is_admin = is_admin
        await flow_client.update_user(user)


async def get_all_users() -> list[UserModel]:
    pass

async def get_user_count() -> int:
    pass


@cached(key_builder=lambda user_id: build_key(user_id))
async def get_user(user_id: int) -> UserSchema:
    async with FlowClient(base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY) as flow_client:
        return await flow_client.get_user(telegram_user_id=user_id)


@cached(key_builder=lambda user_id: build_key(user_id))
async def get_user_by_camunda_user_id(camunda_user_id: str) -> UserSchema:
    async with FlowClient(base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY) as flow_client:
        return await flow_client.get_user(camunda_user_id=camunda_user_id)
