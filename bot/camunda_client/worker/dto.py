from datetime import datetime
from typing import Any

from camunda_client.types_ import BaseDTO, TVariables, Variables


class ExternalTaskDTO(BaseDTO):
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
    process_instance_id: str | None = None
    tenant_id: str | None = None
    retries: int | None = None
    business_key: str | None = None
    variables: Variables
    parsed_variables: dict[str, Any]

    def get_variables(self, type_: type[TVariables]) -> TVariables:
        return type_.model_validate(self.parsed_variables)
