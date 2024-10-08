import uuid
import os
from typing import Callable

from camunda.external_task.external_task_worker import ExternalTaskWorker

ENGINE_URL = os.getenv('ENGINE_URL', 'http://localhost:8080/engine-rest')


def setup_worker(topic: str, handle_task: Callable, config: dict):
    worker_id = f"{topic}_{uuid.uuid4().hex[:8]}"

    ExternalTaskWorker(
        worker_id=worker_id,
        base_url=ENGINE_URL,
        config=config,
    ).subscribe([topic], handle_task)
