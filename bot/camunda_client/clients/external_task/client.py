from collections.abc import Sequence
from datetime import timedelta

import httpx
from pydantic import TypeAdapter

from camunda_client.clients.dto import AuthData
from camunda_client.clients.endpoints import CamundaUrls
from camunda_client.types_ import Variables
from camunda_client.utils import camunda_timedelta, raise_for_status

from .dto import ExternalTaskConfig
from .schemas import (
    CompleteExternalTaskSchema,
    ExtendLockOnExternalTaskSchema,
    ExternalTaskFailureSchema,
    FetchExternalTasksSchema,
    FetchExternalTaskTopicSchema,
    TaskBpmnErrorSchema,
)
from .schemas.response import ExternalTaskSchema


class ExternalTaskClient:
    def __init__(  # noqa: PLR0913
        self,
        worker_id: str,
        base_url: str,
        auth_data: AuthData,
        transport: httpx.AsyncHTTPTransport,
        config: ExternalTaskConfig | None = None,
        urls: CamundaUrls | None = None,
    ) -> None:
        self._worker_id = worker_id
        self._http_client = httpx.AsyncClient(
            base_url=base_url,
            transport=transport,
            auth=httpx.BasicAuth(
                username=auth_data.username,
                password=auth_data.password,
            ),
            headers={"Content-Type": "application/json"},
        )
        self._urls = urls or CamundaUrls()
        self._config = config or ExternalTaskConfig()

    async def fetch_and_lock(
        self,
        topic_names: Sequence[str],
        business_key: str | None = None,
        process_variables: Variables | None = None,
        lock_timeout: timedelta | None = None,
    ) -> Sequence[ExternalTaskSchema]:
        url = self._urls.external_task.fetch_and_lock
        topics = [
            FetchExternalTaskTopicSchema(
                topic_name=topic_name,
                lock_duration=camunda_timedelta(self._config.lock_duration),
                process_variables=process_variables,
                business_key=business_key,
                variables=None,
                has_local_variables=None,
            )
            for topic_name in topic_names
        ]
        schema = FetchExternalTasksSchema(
            worker_id=self._worker_id,
            max_tasks=self._config.max_tasks,
            lock_timeout=camunda_timedelta(
                lock_timeout or self._config.async_response_timeout,
            ),
            topics=topics,
        )
        try:
            response = await self._http_client.post(
                url,
                content=schema.model_dump_json(
                    by_alias=True,
                    exclude_none=True,
                ),
                timeout=60,
            )
        except httpx.ReadTimeout:
            return []

        raise_for_status(response)
        adapter = TypeAdapter(list[ExternalTaskSchema])
        return adapter.validate_python(response.json())

    async def complete(
        self,
        task_id: str,
        *,
        global_variables: Variables | None = None,
        local_variables: Variables | None = None,
    ) -> None:
        url = self._urls.external_task.complete(task_id)
        schema = CompleteExternalTaskSchema(
            worker_id=self._worker_id,
            variables=global_variables,
            local_variables=local_variables,
        )
        content = schema.model_dump_json(
            by_alias=True,
            exclude_none=True,
        )

        response = await self._http_client.post(url, content=content)
        raise_for_status(response)

    async def failure(
        self,
        task_id: str,
        *,
        error_message: str,
        retries: int | None = None,
        error_details: str | None = None,
    ) -> None:
        url = self._urls.external_task.failure(task_id)
        schema = ExternalTaskFailureSchema(
            worker_id=self._worker_id,
            error_message=error_message,
            retries=retries,
            retry_timeout=camunda_timedelta(self._config.retry_timeout),
            error_details=error_details,
        )

        response = await self._http_client.post(
            url,
            content=schema.model_dump_json(
                by_alias=True,
                exclude_none=True,
            ),
        )
        raise_for_status(response)

    async def extend_lock(
        self,
        task_id: str,
        *,
        new_duration: int | None = None,
    ) -> None:
        url = self._urls.external_task.extend_lock(task_id)
        schema = ExtendLockOnExternalTaskSchema(
            worker_id=self._worker_id,
            new_duration=new_duration or camunda_timedelta(self._config.lock_duration),
        )

        response = await self._http_client.post(
            url,
            content=schema.model_dump_json(
                by_alias=True,
                exclude_none=True,
            ),
        )
        raise_for_status(response)

    async def unlock(
        self,
        task_id: str,
    ) -> None:
        url = self._urls.external_task.unlock(task_id)
        response = await self._http_client.post(url)
        raise_for_status(response)

    async def bpmn_error(
        self,
        task_id: str,
        error_code: str,
        error_message: str,
    ) -> None:
        url = self._urls.external_task.bpmn_error(task_id)
        schema = TaskBpmnErrorSchema(
            error_code=error_code,
            error_message=error_message,
        )
        response = await self._http_client.post(
            url,
            content=schema.model_dump_json(
                by_alias=True,
                exclude_none=True,
            ),
        )
        raise_for_status(response)
