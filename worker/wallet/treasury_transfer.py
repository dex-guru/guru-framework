"""
Module for handling wallet treasury transfer tasks from the Camunda workflow engine.
It performs operations such as transferring native tokens from and to (if amount is negative) treasury.

Expected variables:
- `chain_id` (optional, int): The ID of the blockchain network to interact with. Defaults to 261 if not provided.
- `transfer_amount` (required, numeric): The amount of tokens to transfer (positive for sending rewards,
    negative for charging users). Fractional values are supported.
- `camunda_user_id` (required, str): The Camunda user ID associated with the wallet address.

Variables returned:
- `treasury_txhash` (str): The transaction hash of the completed token transfer.
"""

import logging

from camunda.external_task.external_task_worker import ExternalTask
from eth_utils import to_wei

from common.utils import setup_worker
from settings.worker import worker_settings as settings
from wallet.wallet_interfaces import Wallet, WalletI

TOPICS = ["wallet_treasury_transfer", "erc20_treasury_transfer"]
CHAIN_ID_TO_GURU_ADDRESS = {
    1: "0x525574c899a7c877a11865339e57376092168258",
    8453: "0x0f1cfd0bb452db90a3bfc0848349463010419ab2",
}

logging.basicConfig(
    level=settings.LOGGING_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def handle_task(task: ExternalTask):
    logger.info(f"Handling task {task}")
    chain_id = task.get_variable("chain_id")
    camunda_user_id = task.get_variable("camunda_user_id")

    # Retrieve the raw transfer amount and check if it exists.
    transfer_amount_raw = task.get_variable("transfer_amount")
    if transfer_amount_raw is None:
        raise ValueError("transfer amount is required")

    # Convert transfer_amount to a float to support fractional values.
    transfer_amount = float(transfer_amount_raw)
    if transfer_amount == 0:
        raise ValueError("transfer amount is required")

    if not camunda_user_id:
        raise ValueError("Camunda user ID is required")

    # Convert chain_id to integer if provided, or default to 261.
    chain_id = int(chain_id) if chain_id else 261

    treasury_wallet = Wallet.from_key(settings.PRIVATE_KEY, chain_id)
    user_wallet = Wallet.from_user_id(camunda_user_id, "camunda_user_id", chain_id)
    if not user_wallet:
        return task.bpmn_error(
            "PRIVATE_KEY_NOT_FOUND",
            "Private key not found",
            variables={"error": "Private key not found"},
        )
    if task.get_topic_name() == "erc20_treasury_transfer":
        return erc20_treasury_transfer(
            task, treasury_wallet, user_wallet, transfer_amount
        )
    else:
        return native_treasury_transfer(
            task, treasury_wallet, user_wallet, transfer_amount
        )


def erc20_treasury_transfer(
    task: ExternalTask,
    treasury_wallet: WalletI,
    user_wallet: WalletI,
    transfer_amount: float,
):
    try:
        # Convert the absolute value of transfer_amount to wei (GURU decimals is 18 too).
        abs_wei_transfer_amount = to_wei(abs(transfer_amount), "ether")
        token_address = CHAIN_ID_TO_GURU_ADDRESS.get(user_wallet.chain_id)

        if not token_address:
            return task.failure(
                "INVALID_CHAIN_ID",
                f"Invalid chain ID: {user_wallet.chain_id}",
                max_retries=0,
                retry_timeout=0,
            )

        if transfer_amount > 0:
            tx_hash = treasury_wallet.send_erc20(
                user_wallet.address, abs_wei_transfer_amount, token_address
            )
        else:
            tx_hash = user_wallet.send_erc20(
                treasury_wallet.address, abs_wei_transfer_amount, token_address
            )
    except Exception as e:
        logger.error(f"Failed to transfer rewards: {e}")
        return task.bpmn_error(
            "FAILED_TO_TRANSFER_REWARDS",
            f"Failed to transfer rewards: {e}",
            variables={"error": str(e), "treasury_txhash": ""},
        )

    return task.complete(
        {
            "treasury_txhash": tx_hash,
        }
    )


def native_treasury_transfer(
    task: ExternalTask,
    treasury_wallet: WalletI,
    user_wallet: WalletI,
    transfer_amount: float,
):
    try:
        # Convert the absolute value of transfer_amount to wei.
        abs_wei_transfer_amount = to_wei(abs(transfer_amount), "ether")
        if transfer_amount > 0:
            tx_hash = treasury_wallet.send_native(
                user_wallet.address, abs_wei_transfer_amount
            )
        else:
            tx_hash = user_wallet.send_native(
                treasury_wallet.address, abs_wei_transfer_amount
            )
    except Exception as e:
        logger.error(f"Failed to transfer rewards: {e}")
        return task.bpmn_error(
            "FAILED_TO_TRANSFER_REWARDS",
            f"Failed to transfer rewards: {e}",
            variables={"error": str(e), "treasury_txhash": ""},
        )

    return task.complete(
        {
            "treasury_txhash": tx_hash,
        }
    )


if __name__ == "__main__":
    logger.info(f"Starting the {TOPICS} worker...")
    setup_worker(TOPICS, handle_task)
