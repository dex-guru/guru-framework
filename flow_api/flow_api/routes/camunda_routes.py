from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Body, Query, UploadFile, Form, File
from starlette.requests import Request
from starlette.responses import JSONResponse

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from camunda_client import Variables
from camunda_client.clients.engine.schemas import GetTasksFilterSchema, TaskSchema
from camunda_client.clients.engine.schemas.response import (
    ProcessVariablesSchema,
    ProcessInstanceSchema,
    ProcessDefinitionSchema,
    Variable,
)
from camunda_client.clients.schemas import PaginationParams, CountSchema
from configs.app_config import settings
from fa_admin.dependencies import sys_key_depends, sys_key_or_jwt_depends
from services import camunda_service

router = APIRouter()


async def process_definitions_query_params(
    processDefinitionId: str = Query(
        None, description="Filter by process definition id"
    ),
    processDefinitionIdIn: str = Query(
        None, description="Filter by a comma-separated list of process definition ids."
    ),
    name: str = Query(None, description="Filter by the name of the process definition."),
    nameLike: str = Query(
        None, description="Filter by the name that the parameter is a substring of."
    ),
    deploymentId: str = Query(
        None, description="Filter by the deployment the id belongs to."
    ),
    deployedAfter: str = Query(
        None,
        description="Filter by the deployment date after a given date. Format yyyy-MM-dd'T'HH:mm:ss.SSSZ",
    ),
    deployedAt: str = Query(
        None,
        description="Filter by the deployment date before a given date. Format yyyy-MM-dd'T'HH:mm:ss.SSSZ",
    ),
    key: str = Query(None, description="Filter by the key of the process definition."),
    keysIn: str = Query(None, description="Filter by a comma-separated list of keys."),
    keyLike: str = Query(
        None, description="Filter by the key that the parameter is a substring of."
    ),
    category: str = Query(
        None, description="Filter by the category of the process definition."
    ),
    categoryLike: str = Query(
        None, description="Filter by the category that the parameter is a substring of."
    ),
    version: int = Query(
        None, description="Filter by the version of the process definition."
    ),
    latestVersion: bool = Query(
        None, description="Filter by the latest version of the process definition."
    ),
    resourceName: str = Query(
        None, description="Filter by the name of the process definition resource."
    ),
    resourceNameLike: str = Query(
        None,
        description="Filter by the name of the process definition resource that the parameter is a substring of.",
    ),
    startableBy: str = Query(
        None, description="Filter by a user name who is allowed to start the process."
    ),
    active: bool = Query(
        None, description="Filter by the activation state of the process definition."
    ),
    suspended: bool = Query(
        None, description="Filter by the suspension state of the process definition."
    ),
    incidentId: str = Query(None, description="Filter by the incident id."),
    incidentType: str = Query(None, description="Filter by the incident type."),
    incidentMessage: str = Query(None, description="Filter by the incident message."),
    incidentMessageLike: str = Query(
        None,
        description="Filter by the incident message that the parameter is a substring of.",
    ),
    tenantIdIn: str = Query(
        None, description="Filter by a comma-separated list of tenant ids."
    ),
    withoutTenantId: bool = Query(
        None,
        description="Only include process definitions which belong to no tenant. Value may only be true, as false is the default behavior.",
    ),
    includeProcessDefinitionsWithoutTenantId: bool = Query(
        None,
        description="Include process definitions which belong to no tenant. Can be used in combination with tenantIdIn. Value may only be true, as false is the default behavior.",
    ),
    versionTag: str = Query(
        None, description="Filter by the version tag of the process definition."
    ),
    versionTagLike: str = Query(
        None,
        description="Filter by the version tag that the parameter is a substring of.",
    ),
    withoutVersionTag: bool = Query(
        None,
        description="Only include process definitions without a version tag. Value may only be true, as false is the default behavior.",
    ),
    startableInTasklist: bool = Query(
        None, description="Filter by the startable state of the process definition."
    ),
    notStartableInTasklist: bool = Query(
        None, description="Filter by the not startable state of the process definition."
    ),
    startablePermissionCheck: bool = Query(
        None,
        description="Filter by the startable permission check state of the process definition.",
    ),
    sortBy: str = Query(
        None,
        description='Enum: "category" "key" "id" "name" "version" "deploymentId" "deployTime" "tenantId " "versionTag".',
    ),
    sortOrder: str = Query(None, description='Enum: "asc" "desc".'),
    firstResult: int = Query(
        None,
        description="Pagination of results. Specifies the index of the first result to return.",
    ),
    maxResults: int = Query(
        None,
        description="Pagination of results. Specifies the maximum number of results to return.",
    ),
):
    return locals()


@router.get(
    "/process-definition",
    response_model=list[ProcessDefinitionSchema],
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def get_process_definitions(
    request: Request,
    query_params: Annotated[dict, Depends(process_definitions_query_params)],
    auth: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
):
    user_claims = await auth.get_raw_jwt()
    process_definitions = await camunda_service.get_process_definitions(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        variables=query_params,
    )
    return process_definitions


@router.post("/process-definition/key/{key}/start", response_model=ProcessInstanceSchema)
async def start_process_instance_by_key(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
    key: str = Path(..., title="Process definition key"),
    variables: Variables = None,
    business_key: str | None = Body(None, description="Business key"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    process_instance = await camunda_service.start_process_instance(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        key,
        business_key=business_key,
        variables=variables or {},
    )
    return process_instance


@router.get("/task", description="Get User's Tasks", response_model=list[TaskSchema])
async def get_tasks(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    limit: int | None = Query(None, description="Limit pagination parameters"),
    offset: int | None = Query(None, description="Offset pagination parameters"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    if limit is None:
        limit = 10
    if offset is None:
        offset = 0
    pagination_params = PaginationParams(
        limit=limit,
        offset=offset,
    )
    tasks = await camunda_service.get_tasks_for_user(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        pagination=pagination_params,
    )
    # TODO: There are cases when returned other list, dop double fixing
    tasks_return = []
    for task in tasks:
        if task.assignee == user_claims["camunda_user_id"]:
            tasks_return.append(task)
    return tasks_return


@router.post("/task", description="Filter User's Task", response_model=list[TaskSchema])
async def filter_tasks(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    schema: GetTasksFilterSchema | None = Body(None, description="Filter user's tasks"),
    pagination: PaginationParams | None = Body(
        None, description="Pagination parameters"
    ),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    tasks = await camunda_service.get_tasks_for_user(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        schema=schema,
        pagination=pagination,
    )
    # TODO: There are cases when returned other list, dop double fixing
    tasks_return = []
    for task in tasks:
        if task.assignee == user_claims["camunda_user_id"]:
            tasks_return.append(task)
    return tasks_return


@router.get(
    "/task/{task_id}/form-variables", response_model=list[ProcessVariablesSchema]
)
async def get_form_variables(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
    task_id: str = Path(..., title="Task ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    variables = {**request.query_params}
    form_variables = await camunda_service.get_task_form_variables(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        task_id=task_id,
        params=variables,
    )
    return form_variables


@router.post("/task/{task_id}/complete")
async def complete_task(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    task_id: str = Path(..., title="Task ID"),
    variables: Variables | None = None,
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    await camunda_service.complete_task(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        task_id=task_id,
        variables=variables or {},
    )
    return {"message": "Task completed successfully"}


@router.post("/task/{task_id}/variables", response_model=list[Variable])
async def modify_task_variables(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
    task_id: str = Path(..., title="Task ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    variables = {**request.query_params}
    variables = await camunda_service.modify_task_variables(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        task_id=task_id,
        variables=variables,
    )
    return variables


@router.get("/process-instance", response_model=list[ProcessInstanceSchema])
async def get_process_instances(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    query_params = {**request.query_params}
    process_instances = await camunda_service.get_process_instances(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        params=query_params,
    )
    return process_instances


@router.get("/process-instance/count", response_model=CountSchema)
async def get_process_instance_count(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    query_params = {**request.query_params}
    count = await camunda_service.get_process_instances_count(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        params=query_params,
    )
    return count


@router.get("/process-instance/{instance_id}", response_model=ProcessInstanceSchema)
async def get_process_instance(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    instance_id: str = Path(..., title="Process instance ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    process_instance = await camunda_service.get_process_instance(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        instance_id,
    )
    return process_instance


@router.get(
    "/process-instance/{instance_id}/variables",
    response_model=Variables,
)
async def get_process_instance_variables(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    instance_id: str = Path(..., title="Process instance ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    variables = await camunda_service.get_process_instance_variables(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        instance_id,
    )
    return variables


@router.delete("/process-instance/{process_id}")
async def delete_process_instance(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    process_id: str = Path(..., title="Process instance ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    await camunda_service.delete_process_instance(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        process_id,
    )
    return {"message": "Process instance deleted successfully"}


@router.put("/process-instance/{instance_id}/suspended")
async def update_suspension_state_by_id(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    instance_id: str = Path(..., title="Process instance ID"),
    suspended: bool = Body(..., title="Suspended state", embed=True),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    await camunda_service.update_suspension_state(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        instance_id,
        suspended,
    )
    return {"message": "Suspension state updated successfully"}


@router.get(
    "/process-definition/{instance_id}/form-variables", response_model=list[Variable]
)
async def get_start_form_variables(
    request: Request,
    auth: AuthJWT = Depends(AuthJWTBearer()),
    instance_id: str = Path(..., title="Process instance ID"),
):
    await auth.jwt_required()
    user_claims = await auth.get_raw_jwt()
    params = {**request.query_params}
    variables = await camunda_service.get_start_form_variables(
        user_claims["camunda_user_id"],
        user_claims["camunda_key"],
        instance_id,
        params=params,
    )
    return variables


@router.post(
    "/deployment/create", response_model={}, dependencies=[Depends(sys_key_depends)]
)
async def create_deployment(
    token: Annotated[str, Depends(sys_key_depends)],
    tenant_id: Optional[str] = Form(None),
    deployment_source: Optional[str] = Form(None),
    deploy_changed_only: Optional[bool] = Form(False),
    enable_duplicate_filtering: Optional[bool] = Form(False),
    deployment_name: Optional[str] = Form(None),
    deployment_activation_time: Optional[str] = Form(None),
    data: UploadFile = File(...),
):
    deployment_data = {
        "tenant-id": tenant_id,
        "deployment-source": deployment_source,
        "deploy-changed-only": deploy_changed_only,
        "enable-duplicate-filtering": enable_duplicate_filtering,
        "deployment-name": deployment_name,
        "deployment-activation-time": deployment_activation_time,
    }

    file_bytes = await data.read()
    file_name = data.filename
    response = await camunda_service.create_deployment(
        settings.ENGINE_USERNAME,
        settings.ENGINE_PASSWORD,
        deployment_data,
        file_bytes,
        file_name,
    )

    return JSONResponse(content=response)


@router.api_route(
    "/proxy/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def proxy_all_requests(
    request: Request,
    full_path: str,
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
):
    user_claims = await auth.get_raw_jwt()

    camunda_user_id = user_claims["camunda_user_id"]
    camunda_key = user_claims["camunda_key"]

    body = await request.body()

    response = await camunda_service.proxy_request_to_camunda(
        camunda_user_id,
        camunda_key,
        request.method,
        full_path,
        request.query_params,
        body,
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)
