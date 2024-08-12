from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CamundaBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True
        response_model_by_alias = True


class LinkSchema(CamundaBaseModel):
    rel: str | None = None
    href: str | None = None
    method: str | None = None


class ProcessDefinition(CamundaBaseModel):
    id: str
    key: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    version: Optional[int] = None
    resource: Optional[str] = None
    deployment_id: Optional[str] = Field(None, alias="deploymentId")
    diagram: Optional[str] = None
    suspended: Optional[bool] = None
    tenant_id: Optional[str] = Field(None, alias="tenantId")
    version_tag: Optional[str] = Field(None, alias="versionTag")
    history_time_to_live: Optional[int] = Field(None, alias="historyTimeToLive")
    startable_in_tasklist: Optional[bool] = Field(None, alias="startableInTasklist")


class ProcessInstance(CamundaBaseModel):
    id: UUID
    links: Optional[List[LinkSchema]] = None
    definition_id: Optional[str] = Field(None, alias="definitionId")
    business_key: Optional[str] = Field(None, alias="businessKey")
    case_instance_id: Optional[str] = Field(None, alias="caseInstanceId")
    ended: Optional[bool] = None
    suspended: Optional[bool] = None
    tenant_id: Optional[str] = Field(None, alias="tenantId")


class Task(CamundaBaseModel):
    id: str
    links: Optional[List[LinkSchema]] = None
    name: Optional[str] = None
    assignee: Optional[str] = None
    created: Optional[str] = None
    due: Optional[str] = None
    follow_up: Optional[str] = Field(None, alias="followUp")
    delegation_state: Optional[str] = Field(None, alias="delegationState")
    description: Optional[str] = None
    execution_id: Optional[str] = Field(None, alias="executionId")
    owner: Optional[str] = None
    parent_task_id: Optional[str] = Field(None, alias="parentTaskId")
    priority: Optional[int] = None
    process_definition_id: Optional[str] = Field(None, alias="processDefinitionId")
    process_instance_id: Optional[str] = Field(None, alias="processInstanceId")
    task_definition_key: Optional[str] = Field(None, alias="taskDefinitionKey")
    case_execution_id: Optional[str] = Field(None, alias="caseExecutionId")
    case_instance_id: Optional[str] = Field(None, alias="caseInstanceId")
    case_definition_id: Optional[str] = Field(None, alias="caseDefinitionId")
    suspended: Optional[bool] = None
    form_key: Optional[str] = Field(None, alias="formKey")
    tenant_id: Optional[str] = Field(None, alias="tenantId")


class Variable(CamundaBaseModel):
    type: Optional[str] = None
    value: Optional[str] = None
    value_info: Optional[dict] = Field(None, alias="valueInfo")


class TaskCount(CamundaBaseModel):
    count: Optional[int]
