from uuid import UUID

from flow_client.types_ import BaseSchema

class AddUserQuerySchema(BaseSchema):
    id: UUID
    username: str
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    is_admin: bool
    is_suspicious: bool
    camunda_user_id: str | None = None
    camunda_key: UUID | None = None
    telegram_user_id: int | None = None
    webapp_user_id: UUID | None = None
    is_block: bool
    is_premium: bool
