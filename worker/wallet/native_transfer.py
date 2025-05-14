"""
Module for handling wallet native transfer tasks.
It facilitates transferring native tokens to a specified wallet address.

Expected variables:
- `chain_id` (optional, int): The ID of the blockchain network to interact with. Defaults to 261 if not provided.
- `transfer_amount` (required, int): The amount of tokens to transfer.
- `camunda_user_id` (required, str): The Camunda user ID associated with the wallet address for signing the transaction.
- `transfer_to` (required, str): The wallet address to transfer the tokens to.

Variables returned:
- `transfer_txhash` (str): The transaction hash of the completed token transfer.
"""

import logging

from camunda.external_task.external_task_worker import ExternalTask
from eth_utils import to_wei, to_checksum_address

from common.utils import setup_worker
from settings.worker import worker_settings as settings
from wallet.wallet_interfaces import Wallet

TOPIC = "wallet_native_transfer"

logging.basicConfig(
    level=settings.LOGGING_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def handle_task(task: ExternalTask):
    logger.info(f"Handling task {task}")
    chain_id = task.get_variable("chain_id")

    if chain_id:
        chain_id = int(chain_id)
    else:
        chain_id = 261

    try:
        transfer_amount = task.get_variable("transfer_amount")
        if not transfer_amount:
            raise ValueError("transfer amount is required")

        transfer_amount = float(transfer_amount)
        if transfer_amount <= 0:
            raise ValueError(
                f"transfer amount must be positive. Got: {transfer_amount}"
            )

        camunda_user_id = task.get_variable("camunda_user_id")
        if not camunda_user_id:
            raise ValueError("Camunda user ID is required")

        transfer_to = task.get_variable("transfer_to")

        if not transfer_to:
            raise ValueError("Transfer to address is required")

        transfer_to = to_checksum_address(transfer_to)

        account = Wallet.from_user_id(
            camunda_user_id, id_type="camunda_user_id", chain_id=chain_id
        )
        if not account:
            return task.bpmn_error(
                "PRIVATE_KEY_NOT_FOUND",
                "Private key not found",
            )
        tx_hash = account.send_native(transfer_to, to_wei(transfer_amount, "ether"))
    except Exception as e:
        logger.error(f"Failed to transfer rewards: {e}")
        return task.bpmn_error(
            "FAILED_TO_TRANSFER_REWARDS",
            f"Failed to transfer rewards: {e}",
        )
    return task.complete(
        {
            "transfer_txhash": tx_hash,
        }
    )


if __name__ == "__main__":
    logger.info(f"Starting the {TOPIC} worker...")
    setup_worker(TOPIC, handle_task)
