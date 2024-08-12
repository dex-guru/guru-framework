from datetime import datetime
from typing import List
from uuid import UUID

from pytz import utc

from camunda_client.types_ import (
    BaseSchema,
)
from flow_client.utils import get_value


class UserSchema(BaseSchema):
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

    @property
    def user_uuid(self) -> UUID:
        return UUID(get_value(self.id))


class ArtSchema(BaseSchema):
    id: UUID
    name: str
    description: str | None = None
    description_prompt: str | None = None
    created_at: datetime | None = datetime.now(tz=utc)
    img_picture: str | None = None
    type: str
    tags: List[str] | None = None
    parent_id: UUID
    user_id: UUID
    reference_id: UUID
    token_id: int | None = None
    likes: int = 0
    is_liked: bool = False
