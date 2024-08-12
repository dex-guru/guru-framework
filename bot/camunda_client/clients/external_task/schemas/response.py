from datetime import datetime
from typing import Any

from camunda_client.types_ import BaseSchema, Variables
from camunda_client.utils import process_variable


class ExternalTaskSchema(BaseSchema):
    id: str
    worker_id: str
    topic_name: str
    activity_id: str | None = None
    activity_instance_id: str | None = None
    error_message: str | None = None
    execution_id: str | None = None
    lock_expiration_time: datetime | None = None
    process_definition_id: str | None = None
    process_definition_key: str | None = None
    process_definition_version_tag: str | None = None
    process_instance_id: str | None = None
    tenant_id: str | None = None
    retries: int | None = None
    suspended: bool | None = None
    priority: int | None = None
    business_key: str | None = None
    variables: Variables

    @property
    def parsed_variables(self) -> dict[str, Any]:
        return {key: process_variable(schema) for key, schema in self.variables.items()}
