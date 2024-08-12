from uuid import UUID

from camunda_client.types_ import BaseSchema, Variables


class AddUserSchema(BaseSchema):
    username: str
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    is_admin: bool
    is_suspicious: bool
    telegram_user_id: int | None = None
    webapp_user_id: UUID | None = None
    is_block: bool
    is_premium: bool
