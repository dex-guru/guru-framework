import os
from datetime import datetime, timedelta

import requests
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

# Camunda and Warehouse API Configuration
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://localhost:8080/engine-rest')
CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')
WAREHOUSE_API_KEY = os.getenv('WAREHOUSE_API_KEY', 'V49GexNS0E65epx9dUF9t7SreRpSQEh59hQR2ah5')
WAREHOUSE_REST_URL = os.getenv('WAREHOUSE_REST_URL', 'https://api.dev.dex.guru/wh')

NETWORK = "canto"

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


def handle_rsi_task(task: ExternalTask) -> TaskResult:
    """Handle tasks related to RSI Indicator calculations."""
    variables = task.get_variables()
    token_address = variables.get('token_address')
    rsi_period = variables.get('sma_period', 7)

    now = datetime.utcnow()
    datetime_end = now.strftime("%Y-%m-%d %H:%M")
    datetime_start = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M")

    # Prepare the request body for the warehouse API
    body = {
        "parameters": {
            "network": NETWORK,
            "token_address": token_address,
            "datetime_start": datetime_start,
            "datetime_end": datetime_end,
            "window": str(rsi_period)
        }
    }

    # Make an HTTP request to fetch RSI indicators
    response = requests.post(
        f"{WAREHOUSE_REST_URL}/rsi_indicator?api_key={WAREHOUSE_API_KEY}",
        json=body
    )

    rsi_data = response.json()
    variables['rsi_indicator'] = rsi_data
    return task.complete(global_variables=variables)


# Subscribe each worker to their respective topics
if __name__ == '__main__':
    worker = ExternalTaskWorker(
        worker_id="indicator_worker",
        base_url=CAMUNDA_URL,
        config=default_config
    )

    worker.subscribe(['get_rsi_indicator'], handle_rsi_task)
