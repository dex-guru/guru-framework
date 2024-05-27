import os
import requests
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from camunda.variables.variables import Variables

# Camunda and Warehouse API Configuration
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://localhost:8080/engine-rest')
CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')
WAREHOUSE_API_KEY = os.getenv('WAREHOUSE_API_KEY', 'Men6g70IKs69AmWSFeBHMvjXzP7QrqrATcTOOyIW')
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


def handle_get_pass_image(task: ExternalTask) -> TaskResult:
    """Handle tasks related to getting the current price of a token."""
    variables = task.get_variables()
    wallet_address = variables.get('wallet_address')
    src1_art_id = variables.get('src1_art_id')
    src2_art_id = variables.get('src2_art_id')
    print(f"wallet_address: {wallet_address}\nsrc1_art_id: {src1_art_id}\nsrc2_art_id: {src2_art_id}")

    new_variables = {"gen_art_id": src2_art_id, "gen_post": "Share"}
    variables = Variables(new_variables)
    #
    #     # Prepare the request body for the warehouse API
    #     body = {
    #         "parameters": {
    #             "network": NETWORK,
    #             "token_address": token_address
    #         }
    #     }
    #
    #     # Make an HTTP request to fetch the current token price
    #     response = requests.post(
    #         f"{WAREHOUSE_REST_URL}/last_token_price_usd?api_key={WAREHOUSE_API_KEY}",
    #         json=body
    #     )
    #
    #     # Extract the current price data from response
    #     price_data = response.json()
    #     if not price_data:
    #         return task.failure("get last price failed",
    #                             f"failed to get last price in {NETWORK}, token: {token_address}",
    #                             3, 5000)
    #
    #     current_price = price_data[0]['last_price']
    #     variables['current_price'] = float(current_price)
    return task.complete(global_variables=variables)


if __name__ == '__main__':
    worker = ExternalTaskWorker(
        worker_id="pass_image_worker",
        base_url=CAMUNDA_URL,
        config=default_config
    )

    worker.subscribe(['comfy_season_blend'], handle_get_pass_image)