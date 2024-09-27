from pathlib import Path
from time import time

from pydantic import BaseModel, ValidationError
from web3 import Web3
from eth_account import Account

from external_workers.common.utils import setup_worker
from camunda.external_task.external_task import ExternalTask
from config import PRIVATE_KEY, CAMUNDA_CLIENT_CONFIG

TOPIC = 'executeSwapUniswapV3'
VARIABLE_NOT_FOUND_ERR_CODE = "VARIABLE_NOT_FOUND"
VARIABLE_NOT_FOUND_MSG = "Variable '{}' not found"


with open(Path(__file__).parent / 'uniswap_v3_router_abi.json') as f:
    UNISWAP_V3_ROUTER_ABI = f.read()


class Vars(BaseModel):
    rpc_url: str
    uniswap_v3_router_address: str
    token_in: str
    token_out: str
    amount_in: int
    chain_id: int


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
    private_key = PRIVATE_KEY
    account = Account.from_key(private_key)
    wallet_address = account.address

    amount_in = variables.amount_in

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
    setup_worker(TOPIC, handle_task, CAMUNDA_CLIENT_CONFIG)
