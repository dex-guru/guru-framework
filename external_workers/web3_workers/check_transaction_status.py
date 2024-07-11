from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from web3 import Web3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

TOPIC_NAME = os.getenv("TOPIC_NAME", "CheckTransactionConfirmed")
CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://localhost:8080/engine-rest")
CAMUNDA_USERNAME = os.getenv("CAMUNDA_USERNAME", "demo")
CAMUNDA_PASSWORD = os.getenv("CAMUNDA_PASSWORD", "demo")

def set_web3_by_chain_id(chain_id: int):
    global w3
    if chain_id == 261:
        url = "http://new-rpc-gw-prod.dexguru.biz/archive/261"
    elif chain_id == 8453:
        url = "https://base-rpc.publicnode.com"
    elif chain_id == 84532:
        url = "https://sepolia.base.org"
    else:
        url = f"http://rpc-gw-stage.dexguru.biz/full/{chain_id}"
    w3 = Web3(Web3.HTTPProvider(url))
    logger.debug(f"Web3 provider set to {url} for chain_id {chain_id}")

# configuration for the Client
default_config = {
    "auth_basic": {"username": CAMUNDA_USERNAME, "password": CAMUNDA_PASSWORD},
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30,
}

def check_transaction_status(tx_hash: str) -> bool:
    logger.debug(f"Checking transaction status for hash: {tx_hash}")
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    logger.debug(f"Transaction receipt: {receipt}")

    if receipt is None:
        logger.debug("Transaction receipt is None")
        return False

    if receipt["status"] != 1:
        logger.debug(f"Transaction status is {receipt['status']} and not 1")
        return False
    return True

def check_transaction_data(tx_hash: str, value: int, txn_input: bytes) -> bool:
    try:
        logger.debug(f"Checking transaction data for hash: {tx_hash}, value: {value}, input: {txn_input}")
        transaction = w3.eth.get_transaction(tx_hash)
        logger.debug(f"Transaction: {transaction}")
        
        if not transaction:
            logger.debug("Transaction not found")
            return False

        if transaction["value"] != int(value):
            logger.debug(f"Transaction value {transaction['value']} does not match expected value {value}")
            return False

        if transaction["input"] != txn_input:
            logger.debug(f"Transaction input {transaction['input']} does not match expected input {txn_input}")
            return False

        return True
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False

def handle_task(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    tx_hash = variables.get("transactionHash")
    txn_input = variables.get("transactionInput")
    txn_value = variables.get("value")
    chain_id = variables.get("chain_id")
    logger.debug(f"Task variables: tx_hash={tx_hash}, txn_input={txn_input}, txn_value={txn_value}, chain_id={chain_id}")
    
    set_web3_by_chain_id(chain_id)

    if txn_input:
        txn_input = bytes.fromhex(txn_input[2:])
        logger.debug(f"Converted transaction input: {txn_input}")

    if not tx_hash:
        logger.error("Transaction hash is missing from the variables")
        return task.bpmn_error(
            404,
            "Transaction hash is missing from the variables",
        )

    is_transaction_same = check_transaction_data(tx_hash, txn_value, txn_input)
    logger.debug(f"Is transaction same: {is_transaction_same}")

    if not is_transaction_same:
        logger.error("Transaction not confirmed")
        return task.failure(
            "Transaction not confirmed",
            "The transaction has not been confirmed on the blockchain",
            3,
            15000,
        )

    transaction_success = check_transaction_status(tx_hash)
    logger.debug(f"Transaction success: {transaction_success}")
    
    if not transaction_success:
        logger.error("Transaction receipt status is not success in blockchain")
        return task.bpmn_error(
            "transaction_failed_onchain",
            "Transaction receipt status is not success in blockchain",
            variables,
        )
    return task.complete(variables)

if __name__ == "__main__":
    ExternalTaskWorker(
        worker_id="1", base_url=CAMUNDA_URL, config=default_config
    ).subscribe(
        [
            TOPIC_NAME,
        ],
        handle_task,
    )


# from camunda.external_task.external_task import ExternalTask, TaskResult
# from camunda.external_task.external_task_worker import ExternalTaskWorker
# from web3 import Web3
# import os

# TOPIC_NAME = os.getenv("TOPIC_NAME", "CheckTransactionConfirmed")
# CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://localhost:8080/engine-rest")
# CAMUNDA_USERNAME = os.getenv("CAMUNDA_USERNAME", "demo")
# CAMUNDA_PASSWORD = os.getenv("CAMUNDA_PASSWORD", "demo")


# def set_web3_by_chain_id(chain_id: int):
#     global w3
#     if chain_id == 261:
#         url = "http://new-rpc-gw-prod.dexguru.biz/archive/261"
#     elif chain_id == 8453:
#         url = "https://base-rpc.publicnode.com"
#     elif chain_id == 84532:
#         url = "https://sepolia.base.org"
#     else:
#         url = f"http://rpc-gw-stage.dexguru.biz/full/{chain_id}"
#     w3 = Web3(Web3.HTTPProvider(url))


# # configuration for the Client
# default_config = {
#     "auth_basic": {"username": CAMUNDA_USERNAME, "password": CAMUNDA_PASSWORD},
#     "maxTasks": 1,
#     "lockDuration": 10000,
#     "asyncResponseTimeout": 5000,
#     "retries": 3,
#     "retryTimeout": 15000,
#     "sleepSeconds": 30,
# }


# def check_transaction_status(tx_hash: str) -> bool:
#     receipt = w3.eth.get_transaction_receipt(tx_hash)

#     if receipt is None:
#         return False

#     if receipt["status"] != 1:
#         return False
#     return True


# def check_transaction_data(tx_hash: str, value: int, txn_input: bytes) -> bool:
#     try:
#         transaction = w3.eth.get_transaction(tx_hash)
#         if not transaction:
#             return False

#         if transaction["value"] != int(value):
#             return False

#         if transaction["input"] != txn_input:
#             return False

#         return True
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return False


# def handle_task(task: ExternalTask) -> TaskResult:
#     variables = task.get_variables()
#     tx_hash = variables.get("transactionHash")
#     txn_input = variables.get("transactionInput")
#     txn_value = variables.get("value")
#     chain_id = variables.get("chain_id")
#     set_web3_by_chain_id(chain_id)

#     if txn_input:
#         txn_input = bytes.fromhex(txn_input[2:])

#     if not tx_hash:
#         return task.bpmn_error(
#             404,
#             "Transaction hash is missing from the variables",
#         )

#     is_transaction_same = check_transaction_data(tx_hash, txn_value, txn_input)

#     if not is_transaction_same:
#         return task.failure(
#             "Transaction not confirmed",
#             "The transaction has not been confirmed on the blockchain",
#             3,
#             15000,
#         )

#     transaction_success = check_transaction_status(tx_hash)
#     if not transaction_success:
#         return task.bpmn_error(
#             "transaction_failed_onchain",
#             "Transaction receipt status is not success in blockchain",
#             variables,
#         )
#     return task.complete(variables)


# if __name__ == "__main__":
#     ExternalTaskWorker(
#         worker_id="1", base_url=CAMUNDA_URL, config=default_config
#     ).subscribe(
#         [
#             TOPIC_NAME,
#         ],
#         handle_task,
#     )
