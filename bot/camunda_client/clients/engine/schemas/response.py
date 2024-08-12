from datetime import datetime
from typing import Union, Optional
from uuid import UUID

from camunda_client.types_ import (
    BaseSchema,
    MayBeNullableList,
    Variables,
    VariableValueSchema,
)
from camunda_client.utils import get_value

from .enums import DelegationState


class LinkSchema(BaseSchema):
    rel: str | None = None
    href: str | None = None
    method: str | None = None


class ProcessInstanceSchema(BaseSchema):
    id: UUID
    definition_id: str | None = None
    links: MayBeNullableList[LinkSchema]
    business_key: str | None = None
    case_instance_id: str | None = None
    suspended: bool | None = None
    tenant_id: str | None = None


class VariableValueInfo(BaseSchema):
    # Assuming valueInfo might be expanded in the future,
    # but leaving it empty as per the provided example.
    pass


class Variable(BaseSchema):
    type: str
    value: Optional[Union[int, str]]  # Assuming values can be of different types based on the "type" field
    valueInfo: VariableValueInfo


class ProcessVariablesSchema(BaseSchema):
    name: str
    value: Variable
    # Add more variables as needed


class ProcessDefinitionSchema(BaseSchema):
    id: str
    key: str | None = None
    category: str | None = None
    description: str | None = None
    name: str | None = None
    version: int | None = None
    resource: str | None = None
    deployment_id: str | None = None
    diagram: str | None = None
    suspended: bool | None = None
    tenant_id: str | None = None
    version_tag: str | None = None
    history_time_to_live: int | None = None
    startable_in_task_list: bool | None = None
    variables: Variables | None = None


class ProfileSchema(BaseSchema):
    id: str
    first_name: str | None
    last_name: str | None
    email: str | None


class TaskSchema(BaseSchema):
    id: UUID
    name: str
    assignee: str | None = None
    owner: str | None = None
    created: datetime
    due: datetime | None = None
    last_updated: datetime | None = None
    delegation_state: DelegationState | None = None
    description: str | None = None
    execution_id: UUID
    parent_task_id: str | None = None
    priority: int
    process_definition_id: str
    process_instance_id: UUID
    case_execution_id: str | None = None
    case_definition_id: str | None = None
    case_instance_id: str | None = None
    task_definition_key: str | None = None
    suspended: bool
    tenant_id: str | None

    @property
    def assignee_uuid(self) -> UUID:
        return UUID(get_value(self.assignee))


class HistoricTaskInstanceSchema(BaseSchema):
    id: UUID
    process_definition_key: str
    process_definition_id: str
    process_instance_id: UUID
    execution_id: str
    case_definition_key: str | None = None
    case_definition_id: str | None = None
    case_instance_id: str | None = None
    case_execution_id: str | None = None
    activity_instance_id: str | None = None
    name: str | None = None
    description: str | None = None
    delete_reason: str | None = None
    owner: str | None = None
    assignee: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration: int | None = None
    task_definition_key: str
    priority: int | None = None
    due: datetime | None = None
    parent_task_id: str | None = None
    follow_up: datetime | None = None
    tenant_id: str | None = None
    removal_time: datetime | None = None
    root_process_instance_id: UUID | None = None


class VariableInstanceSchema(VariableValueSchema):
    id: str
    name: str
    process_definition_id: str
    process_instance_id: UUID
    execution_id: str
    case_instance_id: str | None = None
    case_execution_id: str | None = None
    task_id: str | None = None
    batch_id: str | None = None
    activity_instance_id: str | None = None
    tenant_id: str | None = None
    error_message: str | None = None
