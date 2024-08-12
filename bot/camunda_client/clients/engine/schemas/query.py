from typing import Any, List
from uuid import UUID

from pydantic import ConfigDict

from camunda_client.types_ import BaseSchema

from .enums import Operator, ProcessInstanceQuerySortEnum, SortOrder


class ConditionQueryParameterSchema(BaseSchema):
    model_config = ConfigDict(use_enum_values=True)

    operator: Operator
    value: Any


class VariableQueryParameterSchema(ConditionQueryParameterSchema):
    name: str | None = None


class ProcessInstanceQuerySortItemSchema(BaseSchema):
    model_config = ConfigDict(use_enum_values=True)

    sort_by: ProcessInstanceQuerySortEnum | None = None
    sort_order: SortOrder | None = None


class FormVariablesQuerySchema(BaseSchema):
    id: UUID  # The id of the process definition is required
    variable_names: str | None = None  # A comma-separated list of variable names to filter by
    deserialize_values: bool = True  # Determines whether to deserialize variable values


class ProcessDefinitionQuerySchema(BaseSchema):
    process_definition_id: str | None = None
    process_definition_id_in: List[str] | None = None
    name: str | None = None
    name_like: str | None = None
    deployment_id: str | None = None
    deployed_after: str | None = None  # Should be datetime in practice
    deployed_at: str | None = None  # Should be datetime in practice
    key: str | None = None
    keys_in: List[str] | None = None
    key_like: str | None = None
    category: str | None = None
    category_like: str | None = None
    version: int | None = None
    latest_version: bool | None = None
    resource_name: str | None = None
    resource_name_like: str | None = None
    startable_by: str | None = None
    active: bool | None = None
    suspended: bool | None = None
    incident_id: str | None = None
    incident_type: str | None = None
    incident_message: str | None = None
    incident_message_like: str | None = None
    tenant_id_in: List[str] | None = None
    without_tenant_id: bool | None = None
    include_process_definitions_without_tenant_id: bool | None = None
    version_tag: str | None = None
    version_tag_like: str | None = None
    without_version_tag: bool | None = None
    startable_in_tasklist: bool | None = None
    not_startable_in_tasklist: bool | None = None
    startable_permission_check: bool | None = None
    sort_by: str | None = None
    sort_order: str | None = None
    first_result: int | None = None
    max_results: int | None = None


class ProcessInstanceQuerySchema(BaseSchema):
    deployment_id: str | None = None
    process_definition_id: str | None = None
    process_definition_key: str | None = None
    process_definition_key_in: list[str] | None = None
    process_definition_key_not_in: list[str] | None = None
    business_key: str | None = None
    business_key_like: str | None = None
    case_instance_id: str | None = None
    super_process_instance: str | None = None
    sub_process_instance: str | None = None
    super_case_instance: str | None = None
    sub_case_instance: str | None = None
    active: bool | None = None
    suspended: bool | None = None
    process_instance_ids: list[str] | None = None
    with_incident: bool | None = None
    incident_id: str | None = None
    incident_type: str | None = None
    incident_message: str | None = None
    incident_message_like: str | None = None
    tenant_id_in: list[str] | None = None
    without_tenant_id: bool | None = None
    process_definition_without_tenant_id: bool | None = None
    activity_id_in: list[str] | None = None
    root_process_instances: bool | None = None
    leaf_process_instances: bool | None = None
    variables: list[VariableQueryParameterSchema] | None = None
    variable_names_ignore_case: bool | None = None
    variable_values_ignore_case: bool | None = None
    or_queries: list["ProcessInstanceQuerySchema"] | None = None
    sorting: list[ProcessInstanceQuerySortItemSchema] | None = None
