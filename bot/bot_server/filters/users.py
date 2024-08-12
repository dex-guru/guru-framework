
from aiogram import types
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from pydantic import BaseModel


class User(BaseModel):
    id: str
    username: str
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    is_admin: bool
    is_suspicious: bool
    camunda_user_id: str | None = None
    camunda_key: str | None = None
    telegram_user_id: int | None = None
    webapp_user_id: str | None = None
    is_block: bool
    is_premium: bool
    # roles: List[str] = []


class UserContextFilter(BaseFilter):
    async def __call__(self, message: types.Message, state: FSMContext):
        telegram_user_id = message.from_user.id

        user = User()
        if not user:
            await message.answer("You are not registered in our system.")
            return False

        # Save user data to state for later use in handlers
        await state.update_data(user=user.to_dict())
        return True
