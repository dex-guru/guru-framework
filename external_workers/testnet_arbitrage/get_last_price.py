import os
from functools import cache

import requests
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

# Camunda and Warehouse API Configuration
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://localhost:8080/engine-rest')
CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')
WAREHOUSE_API_KEY = os.getenv('WAREHOUSE_API_KEY', 'Men6g70IKs69AmWSFeBHMvjXzP7QrqrATcTOOyIW')
WAREHOUSE_REST_URL = os.getenv('WAREHOUSE_REST_URL', 'https://api.dev.dex.guru/wh')
TOPIC_NAME = os.getenv("TOPIC_NAME", "get_target_price")

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

@cache
def get_supported_chains():
    result = {}
    response = requests.post(
        f"{WAREHOUSE_REST_URL}/copy_of_2_chains_supported?api_key=TNH9NjX4yyoFqBms3uwYNJf0j3em2X6QNjZLLhTe",
        json={}
    )

    for item in response.json():
        result[item['value']] = item['name']
    return result


def handle_get_candles_task(task: ExternalTask) -> TaskResult:
    """Handle tasks related to getting the current price of a token."""
    variables = task.get_variables()
    token_address = variables.get('src_token_address')
    chain_id = variables.get('src_chain_id')

    networks = get_supported_chains()

    network = networks.get(chain_id)

    if not network:
        task.failure(f'Cannot get network name for chain: {chain_id}',
                     'Cannot resolve network name from api',
                     max_retries=3,
                     retry_timeout=15000)

    # Prepare the request body for the warehouse API
    body = {
        "parameters": {
            "network": network,
            "token_address": token_address
        }
    }

    # Make an HTTP request to fetch the current token price
    try:
        response = requests.post(
            f"{WAREHOUSE_REST_URL}/last_token_price_usd?api_key={WAREHOUSE_API_KEY}",
            json=body
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        return task.failure("get last price failed",
                            err,
                            max_retries=3,
                            retry_timeout=5000)

    price_data = response.json()
    if not price_data or not price_data[0].get('last_price'):
        return task.failure("get last price failed",
                            f"failed to get last price in {network}, token: {token_address}",
                            3, 5000)

    current_price = price_data[0]['last_price']
    variables['target_price'] = float(current_price)
    return task.complete(variables)


if __name__ == '__main__':
    _ = get_supported_chains()
    worker = ExternalTaskWorker(
        worker_id="last_price_worker",
        base_url=CAMUNDA_URL,
        config=default_config
    )

    worker.subscribe([TOPIC_NAME], handle_get_candles_task)
