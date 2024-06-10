import os

from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from redis import Redis

from config import DEFAULT_CONFIG, CAMUNDA_URL

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
DELAY_TOPIC_NAME = "check_delay"


def check_delay(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    wallet_address = variables.get("wallet_address")
    if redis_client.exists(wallet_address):
        return task.bpmn_error(
            "FAUCET_PROCESS_ERROR", "You can claim tokens once per 24h"
        )
    return task.complete(variables)


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
    ).subscribe([DELAY_TOPIC_NAME], check_delay)
