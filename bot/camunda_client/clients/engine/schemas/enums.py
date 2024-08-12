from enum import Enum


class ProcessInstanceQuerySortEnum(Enum):
    INSTANCE_ID = "instanceId"
    DEFINITION_ID = "definitionId"
    DEFINITION_KEY = "definitionKey"
    BUSINESS_KEY = "businessKey"
    TENANT_ID = "tenantId"


class TaskQuerySortEnum(Enum):
    ASSIGNEE = "assignee"
    CASE_EXECUTION_ID = "caseExecutionId"
    CASE_EXECUTION_VARIABLE = "caseExecutionVariable"
    CASE_INSTANCE_ID = "caseInstanceId"
    CASE_INSTANCE_VARIABLE = "caseInstanceVariable"
    CREATED = "created"
    DESCRIPTION = "description"
    DUE_DATE = "dueDate"
    EXECUTION_ID = "executionId"
    EXECUTION_VARIABLE = "executionVariable"
    FOLLOW_UP_DATE = "followUpDate"
    ID = "id"
    INSTANCE_ID = "instanceId"
    LAST_UPDATED = "lastUpdated"
    NAME = "name"
    NAME_CASE_INSENSITIVE = "nameCaseInsensitive"
    PRIORITY = "priority"
    PROCESS_VARIABLE = "processVariable"
    TASK_VARIABLE = "taskVariable"


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


class Operator(Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTEQ = "gteq"
    LT = "lt"
    LTEQ = "lteq"
    LIKE = "like"
    NOT_LIKE = "notLike"


class DelegationState(Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
