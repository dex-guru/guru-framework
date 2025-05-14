import logging

from camunda.external_task.external_task_worker import ExternalTask
from web3 import Web3, HTTPProvider
from common.utils import setup_worker, get_web3_client_by_chain_id
from settings.worker import worker_settings as settings
from wallet.wallet_interfaces import Wallet, WalletI

APPROVE_TOKEN_FOR_NFT_WORKER = "approve_token"
APPROVE_TOKEN_FOR_USER_WORKER = "approve_token_for_user"
TOPICS = (APPROVE_TOKEN_FOR_NFT_WORKER, APPROVE_TOKEN_FOR_USER_WORKER)


ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

USDT_APPROVE_ABI = [
    # USDT ERC20 contract has the following approve function
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]


def handle_task(task: ExternalTask):
    """
    Entry point for the approve token worker.

    Depending on the topic, loads the appropriate wallet/account and delegates to approve_token.
    Handles both NFT and user wallet approval flows.

    Args:
        task (ExternalTask): The Camunda external task.

    Returns:
        Result of approve_token or error handling.
    """
    camunda_user_id = task.get_variable("camunda_user_id")
    if task.get_topic_name() == APPROVE_TOKEN_FOR_NFT_WORKER:
        w3 = Web3(HTTPProvider(settings.RPC_URL))
        account = w3.eth.account.from_key(settings.NFT_PRIVATE_KEY)
        return approve_token(task, account, w3)
    elif task.get_topic_name() == APPROVE_TOKEN_FOR_USER_WORKER:
        chain_id = task.get_variable("chain_id")
        wallet = Wallet.from_user_id(
            camunda_user_id, "camunda_user_id", chain_id=chain_id
        )
        if not wallet:
            return task.bpmn_error(
                "USER_NOT_FOUND",
                "User not found",
            )
        w3 = get_web3_client_by_chain_id(chain_id)
        return approve_token(task, wallet, w3)


def approve_token(task: ExternalTask, account: WalletI, w3: Web3):
    """
    Handles the logic for ERC-20 token approval.

    - Checks if the current allowance is sufficient.
    - If not, submits an approval transaction.
    - Handles special cases (e.g., USDT fallback).
    - Reports errors to the workflow engine via bpmn_error.

    Args:
        task (ExternalTask): The Camunda external task.
        account (WalletI): The wallet/account to use for approval.
        w3 (Web3): The web3 client.

    Returns:
        Result of task.complete or task.bpmn_error.
    """
    try:
        token_address = Web3.to_checksum_address(task.get_variable("token_address"))
    except Exception as e:
        return task.bpmn_error(
            "APPROVE_TOKEN_FAILED",
            str(e),
            variables={"error": str(e)},
        )
    if token_address.lower() == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee":
        return task.complete(
            {
                "txhash_approve": None,
            }
        )
    token_allowance = task.get_variable("token_allowance")
    if not token_allowance:
        token_allowance = 2**256 - 1  # Max uint256 value
    else:
        token_allowance = int(token_allowance)
    spender_address = Web3.to_checksum_address(task.get_variable("spender_address"))
    chain_id = task.get_variable("chain_id") or settings.CHAIN_ID
    chain_id = int(chain_id)

    try:
        # Initialize ERC-20 and NFT contracts
        erc20_contract = w3.eth.contract(
            address=w3.to_checksum_address(token_address), abi=ERC20_ABI
        )
        # Fetch current gas price dynamically
        gas_price = w3.eth.gas_price
        # Check GURU token allowance
        allowance = erc20_contract.functions.allowance(
            account.address, Web3.to_checksum_address(spender_address)
        ).call()

        is_approved = allowance >= token_allowance

        if not is_approved:
            # If allowance is insufficient, approve the NFT contract to spend GURU tokens
            nonce = account.nonce
            approve_gas = erc20_contract.functions.approve(
                spender_address, token_allowance
            ).estimate_gas({"from": account.address})
            approve_tx = erc20_contract.functions.approve(
                spender_address, token_allowance
            ).build_transaction(
                {
                    "chainId": chain_id,
                    "gas": approve_gas,
                    "gasPrice": gas_price,
                    "nonce": nonce,
                }
            )
            try:
                approve_tx_hash = account.send_transaction(approve_tx)
                approve_receipt = w3.eth.wait_for_transaction_receipt(approve_tx_hash)
                if approve_receipt.status != 1:
                    raise Exception("Approval transaction failed")
            except Exception as e:
                logging.error(f"Failed to approve token: {e}, trying USDT approve")
                erc20_contract = w3.eth.contract(
                    address=w3.to_checksum_address(token_address), abi=USDT_APPROVE_ABI
                )
                approve_gas = erc20_contract.functions.approve(
                    spender_address, token_allowance
                ).estimate_gas({"from": account.address})
                approve_tx = erc20_contract.functions.approve(
                    spender_address, token_allowance
                ).build_transaction(
                    {
                        "chainId": chain_id,
                        "gas": approve_gas,
                        "gasPrice": gas_price,
                        "nonce": nonce,
                    }
                )
                approve_tx_hash = account.send_transaction(approve_tx)
                approve_receipt = w3.eth.wait_for_transaction_receipt(approve_tx_hash)
                if approve_receipt.status != 1:
                    raise Exception("Approval transaction failed")
        else:
            approve_tx_hash = None

        # Return success
        return task.complete(
            {
                "txhash_approve": approve_tx_hash if not is_approved else None,
            }
        )

    except Exception as e:
        logging.error(f"Failed to approve token: {e}")
        return task.bpmn_error(
            "APPROVE_TOKEN_FAILED",
            str(e),
            variables={"error": str(e)},
        )


if __name__ == "__main__":
    setup_worker(TOPICS, handle_task)
