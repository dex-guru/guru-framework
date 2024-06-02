import os
import requests
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

# Camunda API Configuration
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://localhost:8080/engine-rest')
CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')

# External service for response generation
LANGCHAIN_API_URL = os.getenv('LANGCHAIN_API_URL', 'https://api.example.com')


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

def handle_generate_response_task(task: ExternalTask) -> TaskResult:
    """Handle tasks related to generating responses based on selected prompts."""
    variables = task.get_variables()
    dashboard_slug = variables.get('dashboard_slug')
    selected_prompt = variables.get('selected_prompt')
    prompt_suffix = variables.get('prompt_suffix')
    parameters = variables.get('parameters', {})

    # Prepare the request body for generating response based on the selected prompt
    body = {
        "selected_prompt": selected_prompt,
        "dashboard_slug": dashboard_slug,
        "prompt_suffix": prompt_suffix,
        "parameters": parameters
    }

    # Make an HTTP request to generate the response
    response = requests.post(
        f"{LANGCHAIN_API_URL}/endpoints.dashboard_analyze_chain.sequential_chain/run",
        json=body
    )

    # Extract the response data from the response
    response_data = response.json()
    if not response_data:
        return task.failure("Failed to generate response",
                            f"Failed to generate response for prompt: {selected_prompt}",
                            3, 5000)

    response_text = response_data.get('response_text', '')
    variables['response_text'] = response_text
    return task.complete(global_variables=variables)

if __name__ == '__main__':
    worker = ExternalTaskWorker(
        worker_id="response_generation_worker",
        base_url=CAMUNDA_URL,
        config=default_config
    )

    worker.subscribe(['get_gen_response'], handle_generate_response_task)
