import pytest
from unittest.mock import MagicMock, ANY, patch
from camunda.external_task.external_task_worker import ExternalTask
from wallet.approve_token import approve_token
from wallet.wallet_interfaces import WalletI
from web3 import Web3


class AnyNotNull:
    def __eq__(self, other):
        return other is not None

    def __repr__(self):
        return "ANY_NOT_NONE"


@pytest.fixture
def mock_task():
    task = MagicMock(spec=ExternalTask)
    task.get_variable.side_effect = lambda key: {
        "token_address": "0x0000000000000000000000000000000000000000",
        "token_allowance": "1000",
        "spender_address": "0x0000000000000000000000000000000000000001",
        "chain_id": "1",
    }.get(key)
    return task


@pytest.fixture
def mock_account():
    account = MagicMock(spec=WalletI)
    account.address = "0x0000000000000000000000000000000000000002"
    account.nonce = 0
    return account


@pytest.fixture
def mock_web3():
    w3 = MagicMock()
    w3.eth.gas_price = 20000000000
    w3.eth.contract.return_value.functions.allowance.return_value.call.return_value = 0
    w3.eth.get_transaction_count.return_value = 0
    w3.eth.wait_for_transaction_receipt.return_value.status = 1
    return w3


def test_approve_token_allowed(mock_task, mock_account, mock_web3):
    mock_web3.eth.contract.return_value.functions.allowance.return_value.call.return_value = (
        1001
    )
    approve_token(mock_task, mock_account, mock_web3)
    mock_task.complete.assert_called_with({"txhash_approve": None})


def test_approve_token_insufficient_allowance(mock_task, mock_account, mock_web3):
    mock_web3.eth.contract.return_value.functions.allowance.return_value.call.return_value = (
        500
    )
    approve_token(mock_task, mock_account, mock_web3)
    mock_task.complete.assert_called_with({"txhash_approve": ANY})


def test_approve_token_approval_failed(mock_task, mock_account, mock_web3):
    mock_web3.eth.contract.return_value.functions.allowance.return_value.call.return_value = (
        500
    )
    mock_web3.eth.wait_for_transaction_receipt.return_value.status = 0
    approve_token(mock_task, mock_account, mock_web3)
    mock_task.bpmn_error.assert_called_with(
        "APPROVE_TOKEN_FAILED", "Approval transaction failed", variables=ANY
    )


def test_approve_token_native_token_address(mock_task, mock_account, mock_web3):
    mock_task.get_variable.side_effect = lambda key: {
        "token_address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "token_allowance": "1000",
        "spender_address": "0x0000000000000000000000000000000000000001",
        "chain_id": "1",
    }.get(key)
    approve_token(mock_task, mock_account, mock_web3)
    mock_task.complete.assert_called_with({"txhash_approve": None})


def test_approve_token_contract_call_fails(mock_task, mock_account, mock_web3):
    # Simulate exception in allowance call
    mock_web3.eth.contract.return_value.functions.allowance.return_value.call.side_effect = Exception("fail")
    result = approve_token(mock_task, mock_account, mock_web3)
    mock_task.bpmn_error.assert_called_with(
        "APPROVE_TOKEN_FAILED", "fail", variables={"error": "fail"}
    )


def test_approve_token_approval_receipt_failed(mock_task, mock_account, mock_web3):
    # Simulate approval transaction receipt status != 1
    mock_web3.eth.contract.return_value.functions.allowance.return_value.call.return_value = 0
    mock_account.send_transaction.return_value = "0xhash"
    mock_web3.eth.wait_for_transaction_receipt.return_value.status = 0
    result = approve_token(mock_task, mock_account, mock_web3)
    mock_task.bpmn_error.assert_called_with(
        "APPROVE_TOKEN_FAILED", "Approval transaction failed", variables=AnyNotNull()
    )


def test_approve_token_usdt_approve_fails(mock_task, mock_account, mock_web3):
    # Simulate exception in USDT approve fallback
    mock_web3.eth.contract.return_value.functions.allowance.return_value.call.return_value = 0
    mock_account.send_transaction.side_effect = [Exception("fail"), Exception("fail2")]
    result = approve_token(mock_task, mock_account, mock_web3)
    mock_task.bpmn_error.assert_called_with(
        "APPROVE_TOKEN_FAILED", "fail2", variables=AnyNotNull()
    )


def test_approve_token_missing_token_address(mock_account, mock_web3):
    task = MagicMock(spec=ExternalTask)
    task.get_variable.side_effect = lambda key: {
        "token_allowance": "1000",
        "spender_address": "0x0000000000000000000000000000000000000001",
        "chain_id": "1",
    }.get(key)
    approve_token(task, mock_account, mock_web3)
    task.bpmn_error.assert_called()


def test_approve_token_invalid_token_address(mock_task, mock_account, mock_web3):
    # Simulate ValueError in to_checksum_address
    with patch.object(Web3, "to_checksum_address", side_effect=ValueError("bad address")):
        result = approve_token(mock_task, mock_account, mock_web3)
        mock_task.bpmn_error.assert_called_with(
            "APPROVE_TOKEN_FAILED", "bad address", variables=AnyNotNull()
        )
