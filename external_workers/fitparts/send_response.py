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

# Zendesk API Configuration
ZENDESK_URL = os.getenv('ZENDESK_URL', 'https://your_zendesk_instance.zendesk.com/api/v2')
ZENDESK_API_TOKEN = os.getenv('ZENDESK_API_TOKEN', 'your_zendesk_api_token')

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

def handle_update_ticket_task(task: ExternalTask) -> TaskResult:
    """Handle tasks related to updating a Zendesk ticket with a response."""
    variables = task.get_variables()
    ticket_id = variables.get('ticket_id')
    response = variables.get('response')

    if not ticket_id or not response:
        return task.failure(
            "Missing Data",
            "Required variables 'ticket_id' or 'response' are missing.",
            3, 5000
        )

    # Prepare the request body for Zendesk ticket update
    body = {
        "ticket": {
            "comment": {
                "body": f"{response}"
            }
        }
    }

    # Set headers for Zendesk API request
    headers = {
        'Content-Type': 'application/json'
    }

    # Basic authentication with email/token
    auth = ZENDESK_API_TOKEN

    # Make an HTTP request to update the Zendesk ticket
    try:
        zendesk_response = requests.put(
            f"{ZENDESK_URL}/tickets/{ticket_id}.json",
            json=body,
            headers=headers,
            auth=auth
        )

        zendesk_response.raise_for_status()

    except requests.RequestException as e:
        return task.failure(
            "Failed to update Zendesk ticket",
            str(e),
            3, 5000
        )

    return task.complete(global_variables=variables)

if __name__ == '__main__':
    worker = ExternalTaskWorker(
        worker_id="zendesk_update_worker",
        base_url=CAMUNDA_URL,
        config=default_config
    )

    worker.subscribe(['send_zendesk_response'], handle_update_ticket_task)
