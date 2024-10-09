import json
import os
import uuid
from pathlib import Path
from time import time

from camunda.external_task.external_task import ExternalTask
from camunda.external_task.external_task_worker import ExternalTaskWorker
from pydantic import BaseModel, ValidationError
from web3 import Web3

from config import (CAMUNDA_CLIENT_CONFIG, CAMUNDA_URL)

TOPIC = 'executeSwapUniswapV3'
VARIABLE_NOT_FOUND_ERR_CODE = "VARIABLE_NOT_FOUND"
VARIABLE_NOT_FOUND_MSG = "Variable '{}' not found"

WEB3_PK = os.environ.get('WEB3_PK', {'0x0000000000000000000000000000000000000000':
                                     '0000000000000000000000000000000000000000000000000000000000000000'})

with open(Path(__file__).parent / 'uniswap_v3_router_abi.json') as f:
    UNISWAP_V3_ROUTER_ABI = f.read()

with open(Path(__file__).parent / "erc20_abi.json") as fh:
    erc20_abi = json.load(fh)

class Vars(BaseModel):
    rpc_url: str
    uniswap_v3_router_address: str
    token_in: str
    token_out: str
    amount_in: int
    chain_id: int
    wallet_address: str


def get_balances(rpc_url, wallet, token0, token1):

    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token0_contract = web3.eth.contract(
        address=web3.to_checksum_address(token0), abi=erc20_abi
    )
    token1_contract = web3.eth.contract(
        address=web3.to_checksum_address(token1), abi=erc20_abi
    )
    balance0 = token0_contract.functions.balanceOf(
                web3.to_checksum_address(wallet)
            ).call({"to": web3.to_checksum_address(token0)}, 'latest')
    balance1 = token1_contract.functions.balanceOf(
        Web3.to_checksum_address(wallet)
    ).call({"to": web3.to_checksum_address(token1)}, 'latest')

    return balance0, balance1


def approve_maximum_token_spend_if_needed(web3, chain_id, token_address, amount, owner, spender, private_key):
    # Get the ERC20 token contract
    token_contract = web3.eth.contract(
        address=web3.to_checksum_address(token_address),
        abi=erc20_abi
    )

    # Check current allowance
    current_allowance = token_contract.functions.allowance(owner, spender).call()
    max_allowance = 2 ** 256 - 1

    # If the current allowance is less than the maximum, approve the maximum
    if current_allowance < amount:
        # Build the transaction to approve the spender
        approve_txn = token_contract.functions.approve(
            spender,
            max_allowance
        ).build_transaction({
            'chainId': chain_id,
            'gas': 100000,
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(owner),
        })

        # Sign the transaction with the owner's private key
        signed_txn = web3.eth.account.sign_transaction(approve_txn, private_key=private_key)

        # Send the transaction
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Wait for the transaction receipt
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status != 1:
            raise ValueError("Approval transaction failed")

        return receipt


def handle_task(task: ExternalTask):
    try:
        variables = Vars.model_validate(task.get_variables())
    except ValidationError as e:
        return task.bpmn_error(VARIABLE_NOT_FOUND_ERR_CODE, e.json())
    # Connect to Ethereum node via Infura or Alchemy
    web3 = Web3(Web3.HTTPProvider(variables.rpc_url))

    # Uniswap V3 Swap Router contract
    uniswap_v3_router_address = variables.uniswap_v3_router_address

    # Initialize the Uniswap V3 Router contract
    uniswap_v3_router = web3.eth.contract(
        address=web3.to_checksum_address(uniswap_v3_router_address),
        abi=UNISWAP_V3_ROUTER_ABI,
    )


    # Tokens
    token_in = variables.token_in
    token_out = variables.token_out

    fee = 10000  # Uniswap V3 pool fee (3000 = 0.3%)

    # Wallet and account setup
    wallet_address = variables.wallet_address
    private_key = WEB3_PK.get(wallet_address.lower())

    balance0, balance1 = get_balances(variables.rpc_url,
                            wallet_address,
                            web3.to_checksum_address(token_in),
                            web3.to_checksum_address(token_out))

    amount_in = balance0
    if balance0 > balance1 and balance0 > 1000:
        token_in, token_out = token_in, token_out
        amount_in = int(balance0 * 0.99)
    elif balance1 > balance0 and balance1 > 1000:
        token_in, token_out = token_out, token_in
        amount_in = int(balance1 * 0.99)

    if not private_key:
        return task.bpmn_error('PRIVATE_KEY_NOT_FOUND', 'PRIVATE_KEY_NOT_FOUND')

    approve_maximum_token_spend_if_needed(
        web3,
        chain_id=variables.chain_id,
        token_address=token_in,
        amount=amount_in,
        owner=wallet_address,
        spender=uniswap_v3_router_address,
        private_key=private_key
    )

    # Gas price (use a proper provider like Etherscan to get current prices)
    gas_price = web3.eth.gas_price

    # Define the transaction parameters for swapExactInputSingle
    params = {
        'tokenIn': web3.to_checksum_address(token_in),
        'tokenOut': web3.to_checksum_address(token_out),
        'fee': fee,
        'recipient': web3.to_checksum_address(wallet_address),
        'deadline': time() + 600,  # 10 minutes from now
        'amountIn': amount_in,
        'amountOutMinimum': 0,  # set to 1 for simplicity, otherwise you should use Quoter for better estimation
        'sqrtPriceLimitX96': 0,  # no limit on price slippage
    }

    # Build the transaction for the swap
    swap_txn = uniswap_v3_router.functions.exactInputSingle(params).build_transaction(
        {
            'chainId': variables.chain_id,
            'gas': 250000,
            'gasPrice': gas_price,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        }
    )

    # Sign the transaction
    signed_txn = web3.eth.account.sign_transaction(swap_txn, private_key=private_key)

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise ValueError
    return task.complete({'tx_hash': tx_hash.hex()})


if __name__ == '__main__':
    worker_id = f"{TOPIC}_{uuid.uuid4().hex[:8]}"
    ExternalTaskWorker(
        worker_id="1", base_url=CAMUNDA_URL, config=CAMUNDA_CLIENT_CONFIG
    ).subscribe([TOPIC], handle_task)
