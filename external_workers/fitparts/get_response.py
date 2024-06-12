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

def handle_get_generated_prompts_task(task: ExternalTask) -> TaskResult:
    """Handle tasks related to generating prompts."""
    variables = task.get_variables()
    user_name = variables.get('name')
    support_request = variables.get('request')

    # Prepare the request body for the prompt generation API
    body = {
        "user_name": user_name,
        "prompt": support_request
    }

    # Set headers with the API key
    headers = {
        'session': f'{LANGCHAIN_KEY}'
    }

    # Make an HTTP request to fetch the generated prompts
    response = requests.post(
        f"{LANGCHAIN_API_URL}/responses/",
        json=body,
        headers=headers
    )

    # Extract the generated prompts data from the response
    prompts_data = response.json()
    if not prompts_data:
        return task.failure("Failed to generate a response",
                            f"Failed to generate a response for the request: {support_request}",
                            3, 5000)
    variables['response'] = prompts_data['content']
    return task.complete(global_variables=variables)

if __name__ == '__main__':
    worker = ExternalTaskWorker(
        worker_id="response_generation_worker",
        base_url=CAMUNDA_URL,
        config=default_config
    )

    worker.subscribe(['get_gen_response'], handle_get_generated_prompts_task)

