from typing import Any

import pydantic

from camunda_client.types_ import BaseSchema, Variables


class FetchExternalTaskTopicSchema(BaseSchema):
    topic_name: str
    lock_duration: int
    variables: list[str] | None = None
    has_local_variables: bool | None = pydantic.Field(None, alias="localVariables")
    business_key: str | None = None
    process_definition_id: str | None = None
    process_definition_id_in: list[str] | None = None
    process_definition_key: str | None = None
    process_definition_key_in: list[str] | None = None
    process_definition_version_tag: str | None = None
    without_tenant_id: bool | None = None
    tenant_id_in: list[str] | None = None
    process_variables: dict[str, Any] | None = None
    deserialize_values: bool | None = None
    include_extension_properties: bool | None = None


class FetchExternalTasksSchema(BaseSchema):
    worker_id: str
    max_tasks: int
    use_priority: bool | None = None
    lock_timeout: int | None = pydantic.Field(None, alias="asyncResponseTimeout")
    topics: list[FetchExternalTaskTopicSchema] | None = None


class CompleteExternalTaskSchema(BaseSchema):
    worker_id: str
    variables: Variables | None = None
    local_variables: Variables | None = None


class ExternalTaskFailureSchema(BaseSchema):
    worker_id: str
    error_message: str
    error_details: str | None = None
    retries: int | None = None
    retry_timeout: int | None = None
    variables: Variables | None = None
    local_variables: Variables | None = None


class ExtendLockOnExternalTaskSchema(BaseSchema):
    worker_id: str
    new_duration: int


class TaskBpmnErrorSchema(BaseSchema):
    error_code: str
    error_message: str | None
    variables: Variables | None = None
