import logging

from camunda.external_task.external_task import ExternalTask

from settings.worker import worker_settings as settings
from common.utils import setup_worker, get_web3_client_by_chain_id

from wallet.wallet_interfaces import Wallet

TOPIC = "execute_transaction"


def validate_transaction_data(data: dict):
    """
    Validate the transaction data for required fields.

    Args:
        data (dict): The transaction data.

    Returns:
        dict: The validated transaction data.

    Raises:
        ValueError: If any required field is missing.
    """
    required_fields = ["camunda_user_id", "to", "data", "chain_id"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Field '{field}' is required")
    return data


def handle_task(task: ExternalTask):
    """
    Entry point for the execute transaction worker.

    Loads transaction parameters from the task, validates them, prepares and sends
    the transaction, and handles all error cases.

    Args:
        task (ExternalTask): The Camunda external task.

    Returns:
        Result of task.complete or task.bpmn_error.
    """
    variables = task.get_variables()
    camunda_user_id = variables.get("camunda_user_id")
    to_address = variables.get("to")
    wallet_type = variables.get("wallet_type")
    try:
        gas = int(variables.get("gas", 0))
    except ValueError:
        gas = 0
    try:
        gas_price = int(variables.get("gas_price", 0))
    except ValueError:
        gas_price = 0

    value = str(variables.get("value", 0))
    if value.startswith("0x"):
        value = int(value, 16)
    else:
        # handle scientific notation
        value = int(float(value))
    data = variables.get("data")
    chain_id = variables.get("chain_id") or settings.CHAIN_ID
    chain_id = int(chain_id)

    try:
        validate_transaction_data(variables)
    except ValueError as e:
        logging.error(f"Invalid transaction data: {e}")
        return task.bpmn_error(
            "INVALID_DATA",
            str(e),
            variables={"error": str(e)},
        )

    account = Wallet.from_user_id(
        camunda_user_id, "camunda_user_id", chain_id, wallet_type
    )
    if not account:
        logging.error(f"wallet for user {camunda_user_id} not found")
        return task.bpmn_error(
            "PRIVATE_KEY_NOT_FOUND",
            f"Private key not found.",
            variables={"error": f"Private key not found."},
        )
    try:
        w3 = get_web3_client_by_chain_id(chain_id)

        # Handle error in to_checksum_address
        try:
            to_checksum = w3.to_checksum_address(to_address)
        except Exception as e:
            logging.error(f"Invalid to address: {e}")
            return task.bpmn_error(
                "INVALID_TO_ADDRESS",
                str(e),
                variables={"error": str(e)},
            )

        if not gas_price:
            try:
                gas_price = w3.eth.gas_price
            except Exception as e:
                logging.error(f"Failed to fetch gas price: {e}")
                return task.bpmn_error(
                    "GAS_PRICE_FAILED",
                    str(e),
                    variables={"error": str(e)},
                )

        tx = {
            "to": to_checksum,
            "from": account.address,
            "value": value,
            "nonce": account.nonce,
            "gas": int(gas) + 5000,
            "gasPrice": int(int(gas_price) * 1.6),
            "chainId": chain_id,
            "data": data,
        }
    except Exception as e:
        logging.error(f"Failed to prepare transaction: {e}")
        return task.bpmn_error(
            "TRANSACTION_FAILED",
            str(e),
            variables={"error": str(e)},
        )
    try:
        if not gas:
            tx["gas"] = w3.eth.estimate_gas(tx) + 5000
    except Exception as e:
        logging.error(f"Failed to estimate gas: {e}")
        return task.bpmn_error(
            "GAS_ESTIMATION_FAILED",
            str(e),
            variables={"error": str(e)},
        )
    try:
        tx_hash = account.send_transaction(tx)
    except Exception as e:
        logging.error(f"Failed to send transaction: {e}")
        return task.bpmn_error(
            "TRANSACTION_FAILED",
            str(e),
            variables={"error": str(e)},
        )

    return task.complete(
        {"tx_hash": tx_hash},
    )


if __name__ == "__main__":
    setup_worker(TOPIC, handle_task)
