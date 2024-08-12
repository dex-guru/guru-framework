from pydantic import BaseModel


class UserModel(BaseModel):
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