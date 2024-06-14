# external_worker.py
import os
import requests
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

# Camunda API Configuration
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://localhost:8080/engine-rest')
CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')

# External service for prompt generation
LANGCHAIN_API_URL = os.getenv('LANGCHAIN_API_URL', 'http://localhost:8000')
LANGCHAIN_KEY = os.getenv('LANGCHAIN_KEY', 'langcorn-guru')

# Default External Worker Configuration
default_config = {
    "auth_basic": {"username": CAMUNDA_USERNAME, "password": CAMUNDA_PASSWORD},
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30
}


def handle_quickwipe(task: ExternalTask) -> TaskResult:
    """Handle tasks related to generating prompts."""
    variables = task.get_variables()
    if 'response' in variables:
        variables['response'] = None
    if 'request' in variables:
        variables['request'] = None
    return task.complete(global_variables=variables)


if __name__ == '__main__':
    worker = ExternalTaskWorker(
        worker_id="quickwipe_worker",
        base_url=CAMUNDA_URL,
        config=default_config
    )

    worker.subscribe(['quickwipe'], handle_quickwipe)
