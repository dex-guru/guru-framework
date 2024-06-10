import json
import os
from pathlib import Path

import requests
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3
from web3.exceptions import TimeExhausted

from web3_workers.errors import QuoteError

TOPIC_NAME = os.getenv("TOPIC_NAME", "web3_execution")
CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://localhost:8080/engine-rest")
CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')
WEB3_URL = os.getenv("WEB3_URL", "http://rpc-gw-stage.dexguru.biz/full/1")
PRIVATE_KEY = os.getenv(
    "PRIVATE_KEY", "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
)
if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEY is not set")
w3 = Web3(Web3.HTTPProvider(WEB3_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
CHAIN_ID = w3.eth.chain_id
GWEI = 10**9

with open(Path(__file__).parent / "erc20_abi.json") as fh:
    erc20_abi = json.load(fh)


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


def priority_gas_price():
    return w3.eth.gas_price + 3 * GWEI


def handle_task(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    token_address = variables.get("token_address")
    is_backtesting = variables.get("is_backtesting")

    trading_signal = variables.get("trading_signal")
    if not trading_signal:
        return task.complete(variables)

    if is_backtesting:
        # Backtesting logic
        pass
        return task.complete(variables)

    # Live trading logic
    if trading_signal == "buy":
        buy_token = token_address
        sell_token = token_address  # TODO: set the token address to sell
        amount = 0  # TODO: set the amount to sell
        make_trade(buy_token, sell_token, amount)
    elif trading_signal == "sell":
        buy_token = token_address  # TODO: set the token address to buy
        sell_token = token_address
        amount = 0  # TODO: set the amount to sell
        make_trade(buy_token, sell_token, amount)
    return task.complete(variables)


def get_quote(buy_token: str, sell_token: str, amount: int):
    quote_url = f"https://api-trading.dex.guru/v1/market/{CHAIN_ID}/quote"
    params = {
        "buyToken": buy_token,
        "sellToken": sell_token,
        "sellAmount": int(amount),
        "takerAddress": account.address,
        "provider": "paraswap",
    }
    response = requests.get(quote_url, params=params)
    resp = response.json()
    if not resp.get("price"):
        # TODO: add handling
        raise QuoteError(resp.get("error", "Unknown error"))
    return resp


def is_enough_allowance(spender: str, token: ChecksumAddress, amount: int):
    allowance = (
        w3.eth.contract(address=token, abi=erc20_abi)
        .functions.allowance(account.address, spender)
        .call()
    )
    return allowance >= amount


def approve(spender: str, token: ChecksumAddress, amount: int):
    contract = w3.eth.contract(address=token, abi=erc20_abi)
    gas = contract.functions.approve(spender, amount).estimateGas()
    tx = contract.functions.approve(spender, amount).buildTransaction(
        {
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": gas,
            "gasPrice": priority_gas_price(),
            "chainId": CHAIN_ID,
            "value": 0,
        }
    )
    signed_txn = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    try:
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt
    except TimeExhausted:
        # TODO task to cancel TX
        pass
    return None


def cancel_tx(gas_price: int = 0):
    if not gas_price:
        gas_price = priority_gas_price()
    transaction = {
        "to": account.address,
        "from": account.address,
        "value": 0,
        "gas": 21000,  # Gas limit for self transfer
        "gasPrice": gas_price,
        "nonce": w3.eth.get_transaction_count(account.address),
        "data": "0x",
        "chainId": CHAIN_ID,
    }
    signed_tx = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    try:
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        return tx_receipt
    except TimeExhausted:
        cancel_tx(gas_price + 1)


def make_trade(buy_token: str, sell_token: str, amount: int):
    quote = get_quote(buy_token, sell_token, amount)
    # TODO: do we need compare desired price (from warehouse) with quote price?
    data = quote["data"]
    spender = quote["to"]
    sell_token = w3.to_checksum_address(sell_token)
    if not is_enough_allowance(spender, sell_token, amount):
        # TODO: approve task
        approve(spender, sell_token, amount)
    tx = {
        "to": spender,
        "nonce": w3.eth.get_transaction_count(account.address),
        "data": HexBytes(data),
        "gas": int(quote["gas"]),
        "gasPrice": int(quote["gas_price"]) + 3 * GWEI,
        "chainId": CHAIN_ID,
        "value": int(quote["value"]),
    }
    signed_txn = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    try:
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt
    except TimeExhausted:
        # TODO task to cancel TX
        pass
    return None


if __name__ == "__main__":
    ExternalTaskWorker(
        worker_id="web3_transaction_execution",
        base_url=CAMUNDA_URL,
        config=default_config,
    ).subscribe([TOPIC_NAME], handle_task)
