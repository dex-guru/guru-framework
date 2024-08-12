from uuid import UUID

from pydantic import BaseModel


class ORMBaseModel(BaseModel):
    id: int | None = None

    class Config:
        from_attributes = True
        response_model_by_alias = True


class RoleRest(ORMBaseModel):
    name: str
    description: str | None = None


class AdminRest(ORMBaseModel):
    last_login: str | None = None
    email: str
    avatar: str | None = None
    intro: str | None = None


class UserRest(ORMBaseModel):
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
    # roles: List[str] = []


class ConfigRest(ORMBaseModel):
    label: str
    key: str
    value: dict | None = None
    status: int


class AuthTokenRest(BaseModel):
    access_token: str
    refresh_token: str
