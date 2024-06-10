import logging
import os

import requests
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from web3 import Web3

CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://localhost:8080/engine-rest")
API_URL = os.getenv("API_URL", "http://localhost:8000")
CAMUNDA_USERNAME = os.getenv("CAMUNDA_USERNAME", "demo")
CAMUNDA_PASSWORD = os.getenv("CAMUNDA_PASSWORD", "demo")
OPENSEA_API_KEY = os.getenv("OPENSEA_API_KEY", "secret")
SYS_KEY = os.getenv("SYS_KEY", "secret")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CHAIN_ID_TO_CHAIN_NAME = {
    '8453': 'base',
    '1': 'ethereum',
}

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

NFT_ADDRESSES = (
    '0x872ef2bfe4efc19ba4e21e36f4cadac4f8c92ede',
    '0xe41eab3053ddf33ebe071fecfe42ae5332a9eea3',
    '0xeb8ae9ed9df8bff58f9d364eef3c4986f4331d1e',
)


def set_web3_by_chain_id(chain_id: int):
    global w3
    if chain_id == 261:
        url = "http://new-rpc-gw-prod.dexguru.biz/archive/261"
    elif chain_id == 8453:
        url = "https://base-rpc.publicnode.com"
    else:
        url = f"http://rpc-gw-stage.dexguru.biz/full/{chain_id}"
    w3 = Web3(Web3.HTTPProvider(url))


def get_nft_token_id(tx_hash: str) -> int:
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    logs = receipt["logs"]
    for log in logs:
        if (
            log["topics"][0].hex().lower()
            == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            and log['address'].lower() in NFT_ADDRESSES
        ):
            return int(log.topics[3].hex(), 16)
    logger.info("No NFT token id found in the transaction logs")


def store_token_id_and_art_id(token_id: int, art_id: str, chain_id: int) -> None:
    url = f"{API_URL}/seasons/2/chain/{chain_id}/token/{token_id}/art/{art_id}"
    resp = requests.post(url, headers={"X-SYS-KEY": SYS_KEY})
    resp.raise_for_status()


def refresh_opensea_metadata(token_id: int, chain_id: int) -> None:
    chain = "base"
    address = '0xeb8ae9ed9df8bff58f9d364eef3c4986f4331d1e'
    url = f'https://api.opensea.io/api/v2/chain/{chain}/contract/{address}/nfts/{token_id}/refresh'
    resp = requests.post(url, headers={"x-api-key": OPENSEA_API_KEY})
    resp.raise_for_status()


def handle_task(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    tx_hash = variables.get("transactionHash")
    art_id = variables.get("gen_art_id")
    chain_id = variables.get("chain_id")
    set_web3_by_chain_id(chain_id)
    logger.info(
        f"Getting NFT token id. art_id: {art_id} tx_hash: {tx_hash} chain_id: {chain_id}",
    )
    if not tx_hash or not art_id or not chain_id:
        logger.error("transactionHash or get_art_id or chain_id is missing")
        return task.failure(
            "MISSING_VARIABLES",
            "transactionHash or get_art_id or chain_id is missing",
            max_retries=3,
            retry_timeout=5000,
        )
    try:
        token_id = get_nft_token_id(tx_hash)
    except Exception as e:
        logger.error(f"Failed to get NFT token id: {e}")
        return task.failure(
            "FAILED_TO_GET_NFT_TOKEN_ID",
            f"Failed to get NFT token id: {e}",
            max_retries=3,
            retry_timeout=5000,
        )
    if token_id is None:
        return task.failure(
            "FAILED_TO_GET_NFT_TOKEN_ID",
            "Failed to get NFT token id",
            max_retries=3,
            retry_timeout=5000,
        )
    try:
        store_token_id_and_art_id(token_id, art_id, chain_id)
    except Exception as e:
        logger.error(f"Failed to store token id and art id: {e}")
        return task.failure(
            "FAILED_TO_STORE_TOKEN_ID_AND_ART_ID",
            f"Failed to store token id and art id: {e}",
            max_retries=3,
            retry_timeout=5000,
        )
    try:
        refresh_opensea_metadata(token_id, chain_id)
    except Exception as e:
        logger.error(f"Failed to refresh opensea metadata: {e}")
    logger.info(f"Got NFT token id: {token_id}")
    variables["nft_token_id"] = token_id
    variables["transactionHash"] = tx_hash
    variables["chain_id"] = chain_id
    logger.info(f"Returning variables: {variables}")
    return task.complete(variables)


if __name__ == "__main__":
    logger.info("Starting the worker...")
    ExternalTaskWorker(
        worker_id="store_token_id_and_art_id",
        base_url=CAMUNDA_URL,
        config=default_config,
    ).subscribe(
        [
            'StoreTokenIdAndImage',
        ],
        handle_task,
    )
