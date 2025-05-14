"""
This module creates new wallets with private keys and mnemonics, encrypts sensitive data,
and stores the wallet information in the flow API.

Expected variables:
- `camunda_user_id` (required, str): The Camunda user ID for which the wallet will be generated.

Variables returned:
- `wallet_address` (str): The generated wallet address.

Error Handling:
- Raises a BPMN error (`USER_EXISTS`) if a wallet already exists for the given `camunda_user_id`.
- Fails the task if the wallet cannot be stored in the backend system, with details of the error included.
"""

import logging

from camunda.external_task.external_task_worker import ExternalTask

from common.utils import setup_worker
from settings.worker import worker_settings as settings
from wallet.wallet_interfaces import Wallet

TOPIC = "wallet_generate"

logging.basicConfig(
    level=settings.LOGGING_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def handle_task(task: ExternalTask):
    """
    Handles the wallet generation task for a given user.

    Workflow:
    - Checks if a wallet already exists for the provided `camunda_user_id`.
      - If it exists, raises a BPMN error with the existing wallet address.
    - If a `ref_user_id` is provided, fetches the referral wallet address.
    - Creates a new wallet for the user if none exists.
    - Attempts to save the new wallet.
      - If saving fails, marks the task as failed with error details.
    - On success, completes the task and returns the new wallet address (and referral address if applicable).

    Args:
        task (ExternalTask): The Camunda external task containing user variables.

    Returns:
        The result of `task.complete`, `task.bpmn_error`, or `task.failure` depending on the outcome.

    Raises:
        None directly. Errors are communicated via BPMN error or task failure.
    """
    logger.info(f"Handling task {task}")
    camunda_user_id = task.get_variable("camunda_user_id")

    account = Wallet.from_user_id(camunda_user_id, "camunda_user_id", settings.CHAIN_ID)

    ref_user_id = task.get_variable("ref_user_id")

    ref_wallet_address = None
    if ref_user_id:
        logger.info(f"Referral user ID: {ref_user_id}")
        ref_wallet = Wallet.from_user_id(ref_user_id, "user_id", settings.CHAIN_ID)
        ref_wallet_address = ref_wallet.address.lower()

    if account:
        return task.bpmn_error(
            "USER_EXISTS",
            "User already exists",
            variables={
                "wallet_address": account.address.lower(),
                "ref_wallet_address": ref_wallet_address,
            },
        )
    account = Wallet.create(
        camunda_user_id, settings.WALLET_GENERATION_TYPE, settings.CHAIN_ID
    )
    try:
        account.save()
    except Exception as e:
        return task.failure(
            error_message=f"Failed to store wallet: {e}",
            error_details={"address": account.address, "error": str(e)},
            max_retries=3,
            retry_timeout=1000,
        )
    return task.complete(
        {
            "wallet_address": account.address.lower(),
            "ref_wallet_address": ref_wallet_address,
        }
    )


if __name__ == "__main__":
    logger.info(f"Starting the {TOPIC} worker...")
    setup_worker(TOPIC, handle_task)
