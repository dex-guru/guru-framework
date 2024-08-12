from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import Field
from pytz import utc

from fa_admin.rest_models.api_rest_models import ORMBaseModel


class ArtRest(ORMBaseModel):
    id: UUID
    name: str
    description: str | None = None
    description_prompt: str | None = None
    created_at: datetime | None = datetime.now(tz=utc)
    img_picture: str | None = None
    type: str = Field(..., alias="type")
    tags: List | None = None
    parent_id: UUID
    user_id: UUID
    reference_id: UUID
    token_id: int | None = None
    likes: int = 0
    is_liked: bool = False


class ArtCollectionRest(ORMBaseModel):
    id: UUID
    name: str
    symbol: str | None = None
    base_uri: str | None = None
    created_at: datetime
    type: str = Field(..., alias="type")
    user_id: UUID
    arts: List


class EventRest(ORMBaseModel):
    id: UUID
    name: str
    description: str | None = None
    type: str = Field(..., alias="type")
    address: str | None = None
    location: str | None = None
    img_event_cover: str | None = None
    user_id: UUID
    reference_id: UUID
    collections: dict
