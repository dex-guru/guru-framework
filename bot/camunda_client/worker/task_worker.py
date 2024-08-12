import asyncio
import contextlib
from collections.abc import AsyncIterator
from datetime import timedelta
from types import TracebackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camunda_client.clients import ExternalTaskClient

from .context import ExternalTaskContext
from .dto import ExternalTaskDTO
from .topic_consumer import TopicConsumer


class ExternalTaskWorker:
    def __init__(
        self,
        client: "ExternalTaskClient",
        pull_interval: timedelta,
    ) -> None:
        self._consumers: dict[str, TopicConsumer] = {}
        self._pull_interval = pull_interval
        self._client = client

        self._tg = asyncio.TaskGroup()
        self._closing = asyncio.Event()

    async def __aenter__(self) -> None:
        await self._tg.__aenter__()
        self._tg.create_task(self._pull_tasks())

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._closing.set()
        await self._tg.__aexit__(exc_type, exc_val, exc_tb)

    async def _pull_tasks(self) -> None:
        while True:
            if self._consumers:
                tasks = await self._client.fetch_and_lock(
                    topic_names=list(self._consumers),
                )

                for task in tasks:
                    consumer = self._consumers[task.topic_name]
                    consumer.task_contexts.append(
                        ExternalTaskContext(
                            client=self._client,
                            task=ExternalTaskDTO.model_validate(task),
                        ),
                    )
                    consumer.new_task_event.set()

            await self._wait()

            if self._closing.is_set():
                return

    async def _wait(self) -> None:
        _, pending = await asyncio.wait(
            [
                asyncio.create_task(
                    asyncio.sleep(self._pull_interval.total_seconds()),
                ),
                asyncio.create_task(self._closing.wait()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    @contextlib.asynccontextmanager
    async def subscribe(
        self,
        topic: str,
    ) -> AsyncIterator[AsyncIterator[ExternalTaskContext]]:
        topic_consumer = TopicConsumer(closing=self._closing)

        if topic in self._consumers:
            raise ValueError

        self._consumers[topic] = topic_consumer

        yield topic_consumer

        del self._consumers[topic]
