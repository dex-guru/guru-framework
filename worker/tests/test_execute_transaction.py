import pytest
from unittest.mock import patch, MagicMock, ANY
from wallet import execute_transaction

@patch("wallet.execute_transaction.Wallet")
@patch("wallet.execute_transaction.get_web3_client_by_chain_id")
@patch("wallet.execute_transaction.settings")
def test_execute_transaction_valid(mock_settings, mock_get_web3, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variables.return_value = {
        "camunda_user_id": "user_id",
        "to": "0xdef",
        "wallet_type": "guru",
        "gas": "21000",
        "gas_price": "100",
        "value": "1000",
        "data": "0x",
        "chain_id": 261,
    }
    mock_account = MagicMock()
    mock_account.address = "0xabc"
    mock_account.nonce = 1
    mock_account.send_transaction.return_value = "0xhash"
    mock_wallet.from_user_id.return_value = mock_account
    mock_w3 = MagicMock()
    mock_w3.eth.gas_price = 100
    mock_w3.to_checksum_address.return_value = "0xdef"
    mock_get_web3.return_value = mock_w3
    result = execute_transaction.handle_task(mock_task)
    assert result[0] == mock_task.complete.return_value or result == mock_task.complete.return_value

@patch("wallet.execute_transaction.Wallet")
def test_execute_transaction_invalid_data(mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variables.return_value = {"to": "0xdef"}  # missing required fields
    result = execute_transaction.handle_task(mock_task)
    assert mock_task.bpmn_error.called

@patch("wallet.execute_transaction.Wallet")
def test_execute_transaction_wallet_not_found(mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variables.return_value = {
        "camunda_user_id": "user_id",
        "to": "0xdef",
        "wallet_type": "guru",
        "gas": "21000",
        "gas_price": "100",
        "value": "1000",
        "data": "0x",
        "chain_id": 261,
    }
    mock_wallet.from_user_id.return_value = None
    result = execute_transaction.handle_task(mock_task)
    assert mock_task.bpmn_error.called

@patch("wallet.execute_transaction.Wallet")
@patch("wallet.execute_transaction.get_web3_client_by_chain_id")
@patch("wallet.execute_transaction.settings")
def test_execute_transaction_validation_error(mock_settings, mock_get_web3, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variables.return_value = {"to": "0xdef"}  # missing required fields
    result = execute_transaction.handle_task(mock_task)
    mock_task.bpmn_error.assert_called_with(
        "INVALID_DATA", ANY, variables=ANY
    )

@patch("wallet.execute_transaction.Wallet")
@patch("wallet.execute_transaction.get_web3_client_by_chain_id")
@patch("wallet.execute_transaction.settings")
def test_execute_transaction_preparation_exception(mock_settings, mock_get_web3, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variables.return_value = {
        "camunda_user_id": "user_id",
        "to": "0xdef",
        "wallet_type": "guru",
        "gas": "21000",
        "gas_price": "100",
        "value": "1000",
        "data": "0x",
        "chain_id": 261,
    }
    mock_wallet.from_user_id.return_value = MagicMock(address="0x0000000000000000000000000000000000000001", nonce=1)
    mock_get_web3.side_effect = Exception("fail prepare")
    result = execute_transaction.handle_task(mock_task)
    mock_task.bpmn_error.assert_called_with(
        "TRANSACTION_FAILED", "fail prepare", variables=ANY
    )

@patch("wallet.execute_transaction.Wallet")
@patch("wallet.execute_transaction.get_web3_client_by_chain_id")
@patch("wallet.execute_transaction.settings")
def test_execute_transaction_gas_estimation_exception(mock_settings, mock_get_web3, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variables.return_value = {
        "camunda_user_id": "user_id",
        "to": "0xdef",
        "wallet_type": "guru",
        "gas": "0",
        "gas_price": "100",
        "value": "1000",
        "data": "0x",
        "chain_id": 261,
    }
    mock_account = MagicMock(address="0x0000000000000000000000000000000000000001", nonce=1)
    mock_wallet.from_user_id.return_value = mock_account
    mock_w3 = MagicMock()
    mock_w3.eth.gas_price = 100
    mock_w3.to_checksum_address.return_value = "0xdef"
    mock_w3.eth.estimate_gas.side_effect = Exception("fail gas")
    mock_get_web3.return_value = mock_w3
    result = execute_transaction.handle_task(mock_task)
    mock_task.bpmn_error.assert_called_with(
        "GAS_ESTIMATION_FAILED", "fail gas", variables=ANY
    )

@patch("wallet.execute_transaction.Wallet")
@patch("wallet.execute_transaction.get_web3_client_by_chain_id")
@patch("wallet.execute_transaction.settings")
def test_execute_transaction_send_transaction_exception(mock_settings, mock_get_web3, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variables.return_value = {
        "camunda_user_id": "user_id",
        "to": "0xdef",
        "wallet_type": "guru",
        "gas": "21000",
        "gas_price": "100",
        "value": "1000",
        "data": "0x",
        "chain_id": 261,
    }
    mock_account = MagicMock(address="0x0000000000000000000000000000000000000001", nonce=1)
    mock_account.send_transaction.side_effect = Exception("fail send")
    mock_wallet.from_user_id.return_value = mock_account
    mock_w3 = MagicMock()
    mock_w3.eth.gas_price = 100
    mock_w3.to_checksum_address.return_value = "0xdef"
    mock_get_web3.return_value = mock_w3
    result = execute_transaction.handle_task(mock_task)
    mock_task.bpmn_error.assert_called_with(
        "TRANSACTION_FAILED", "fail send", variables=ANY
    ) 