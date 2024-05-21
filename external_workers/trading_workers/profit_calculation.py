import os
import requests
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

# Camunda and Warehouse API Configuration
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://localhost:8080/engine-rest')
CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')

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


def handle_task(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    current_price = float(variables.get('current_price'))
    stop_loss_percentage = float(variables.get('stop_loss')) / 100
    take_profit_percentage = float(variables.get('take_profit')) / 100
    order_amount_usd = float(variables.get('order_amount_usd'))
    token_amount = float(variables.get('token_amount'))

    # Calculate initial deal price
    deal_price = order_amount_usd / token_amount

    # Calculate stop loss and take profit prices
    stop_loss_price = deal_price * (1 - stop_loss_percentage)
    take_profit_price = deal_price * (1 + take_profit_percentage)

    # Trailing stop logic
    if current_price > stop_loss_price:
        # Adjust the stop loss price to be 2% above the new current price
        stop_loss_price = current_price * (1 - 0.02)

    # Check if current price triggers stop loss or take profit
    if current_price <= stop_loss_price or current_price >= take_profit_price:
        variables['close_position'] = True
    else:
        variables['close_position'] = False
    return task.complete(variables)


if __name__ == '__main__':
    worker = ExternalTaskWorker(
        worker_id="profit_calculation_worker",
        base_url=CAMUNDA_URL,
        config=default_config
    )

    worker.subscribe(['sltp_calculation'], handle_task)
