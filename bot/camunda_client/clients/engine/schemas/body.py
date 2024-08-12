from uuid import UUID

from camunda_client.types_ import BaseSchema, Variables

from .enums import SortOrder, TaskQuerySortEnum
from .response import ProfileSchema


class StartProcessInstanceSchema(BaseSchema):
    business_key: str | None = None
    variables: Variables | None = None


class ClaimTaskSchema(BaseSchema):
    user_id: str


class SortSchema(BaseSchema):
    sort_by: TaskQuerySortEnum | None = None
    sort_order: SortOrder | None = None


class GetTasksFilterSchema(BaseSchema):
    assignee: str | None = None
    candidate_group: str | None = None
    candidate_user: str | None = None
    sorting: SortSchema | None = None
    process_instance_id: UUID | None = None
    process_instance_business_key: str | None = None
    process_instance_business_key_in: list[str] | None = None
    process_definition_key: str | None = None
    process_definition_key_in: str | None = None


class GetHistoryTasksFilterSchema(BaseSchema):
    process_instance_id: UUID | None = None
    sorting: SortSchema | None = None
    unfinished: bool = False


class SetAssigneeTaskSchema(BaseSchema):
    user_id: str


class SendCorrelationMessageSchema(BaseSchema):
    message_name: str
    business_key: str | None = None
    process_instance_id: UUID | None = None

    tenant_id: str | None = None
    without_tenant_id: bool = False

    correlation_keys: Variables | None = None
    local_correlation_keys: Variables | None = None
    process_variables: Variables | None = None
    process_variables_local: Variables | None = None

    all: bool = False
    result_enabled: bool = False
    variables_in_result_enabled: bool = False


class CredentialsSchema(BaseSchema):
    password: str


class CreateUserSchema(BaseSchema):
    profile: ProfileSchema
    credentials: CredentialsSchema


class CreateGroupMemberSchema(BaseSchema):
    user_id: str
    group_id: str
