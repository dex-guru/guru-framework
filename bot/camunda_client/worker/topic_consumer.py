import asyncio
from collections.abc import Sequence

from .context import ExternalTaskContext


class TopicConsumer:
    def __init__(self, closing: asyncio.Event) -> None:
        self.task_contexts: list[ExternalTaskContext] = []
        self.new_task_event = asyncio.Event()
        self.closing = closing

    def __aiter__(self):
        return self

    async def __anext__(self) -> ExternalTaskContext:
        _, pending = await asyncio.wait(
            [
                asyncio.create_task(self.new_task_event.wait()),
                asyncio.create_task(self.closing.wait()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

        if self.closing.is_set():
            await self._unlock(self.task_contexts)
            raise StopAsyncIteration

        await self.new_task_event.wait()

        task_context = self.task_contexts.pop()
        if not self.task_contexts:
            self.new_task_event.clear()

        return task_context

    async def _unlock(self, task_contexts: Sequence[ExternalTaskContext]) -> None:
        for ctx in task_contexts:
            await ctx.unlock_task()
