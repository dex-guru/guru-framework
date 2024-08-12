import traceback
from types import TracebackType
from typing import TYPE_CHECKING

from camunda_client.exceptions import InvalidStateError

if TYPE_CHECKING:
    from camunda_client.clients import ExternalTaskClient
from camunda_client.types_ import Variables

from .dto import ExternalTaskDTO


class ExternalTaskContext:
    def __init__(
        self,
        client: "ExternalTaskClient",
        task: ExternalTaskDTO,
    ) -> None:
        self._client = client
        self._task = task
        self._closed: bool = False

    async def __aenter__(self) -> ExternalTaskDTO:
        return self._task

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._closed:
            return

        if exc_val:
            error_message = f"{exc_val.__class__.__qualname__}"
            error_details = "".join(traceback.format_exception(exc_val))
            await self._client.failure(
                self._task.id,
                error_message=error_message,
                error_details=error_details,
            )
        else:
            await self._client.complete(self._task.id)

    async def unlock_task(self) -> None:
        await self._client.unlock(self._task.id)

    async def complete(
        self,
        global_variables: Variables | None = None,
        local_variables: Variables | None = None,
    ) -> None:
        if self._closed:
            msg = "TaskContext is already closed"
            raise InvalidStateError(msg)

        await self._client.complete(
            self._task.id,
            global_variables=global_variables,
            local_variables=local_variables,
        )
        self._closed = True

    async def fail(
        self,
        error_message: str,
        retries: int | None = None,
        error_details: str | None = None,
    ) -> None:
        if self._closed:
            msg = "TaskContext is already closed"
            raise InvalidStateError(msg)

        await self._client.failure(
            self._task.id,
            error_message=error_message,
            retries=retries,
            error_details=error_details,
        )
        self._closed = True
