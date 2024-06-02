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
    dashboard_slug = variables.get('dashboard_slug')
    chat_logs = variables.get('chat_logs')
    parameters = variables.get('parameters', {})

    # Prepare the request body for the prompt generation API
    body = {
        "dashboard_slug": dashboard_slug,
        "chat_logs": chat_logs,
        "parameters": parameters
    }

    # Set headers with the API key
    headers = {
        'session': f'{LANGCHAIN_KEY}'
    }

    # Make an HTTP request to fetch the generated prompts
    response = requests.post(
        f"{LANGCHAIN_API_URL}/prompts/",
        json=body,
        headers=headers
    )

    # Extract the generated prompts data from the response
    prompts_data = response.json()
    if not prompts_data or 'prompts' not in prompts_data:
        return task.failure("Failed to generate prompts",
                            f"Failed to generate prompts for dashboard: {dashboard_slug}",
                            3, 5000)

    generated_prompts = prompts_data['prompts']
    variables['generated_prompts'] = generated_prompts
    return task.complete(global_variables=variables)

if __name__ == '__main__':
    worker = ExternalTaskWorker(
        worker_id="prompt_generation_worker",
        base_url=CAMUNDA_URL,
        config=default_config
    )

    worker.subscribe(['get_gen_prompts'], handle_get_generated_prompts_task)
