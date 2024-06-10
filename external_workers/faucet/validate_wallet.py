import os

from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from web3 import Web3
from redis import Redis

from config import DEFAULT_CONFIG, CAMUNDA_URL, WEB3_URL

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

VALIDATE_TOPIC_NAME = os.getenv("TOPIC_NAME", "validate_wallet_address")
w3 = Web3(Web3.HTTPProvider(WEB3_URL))


def handle_validate_task(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    wallet_address = variables.get("wallet_address")
    if not is_valid_wallet_address(wallet_address):
        return task.bpmn_error(
            "FAUCET_PROCESS_ERROR", "Wallet is not eligible to get tokens"
        )
    variables["wallet_address"] = w3.to_checksum_address(wallet_address)
    return task.complete(variables)


def is_valid_wallet_address(wallet_address: str) -> bool:
    if not w3.is_address(wallet_address):
        return False
    return True


if __name__ == "__main__":
    redis_client = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )
    worker = ExternalTaskWorker(
        worker_id="validate_wallet_address",
        base_url=CAMUNDA_URL,
        config=DEFAULT_CONFIG,
    ).subscribe([VALIDATE_TOPIC_NAME], handle_validate_task)
