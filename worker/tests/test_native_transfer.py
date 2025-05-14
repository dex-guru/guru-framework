import pytest
from unittest.mock import patch, MagicMock
from wallet import native_transfer

@patch("wallet.native_transfer.Wallet")
@patch("wallet.native_transfer.to_checksum_address")
def test_native_transfer_success(mock_to_checksum, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {
        "chain_id": 261,
        "transfer_amount": 1.0,
        "camunda_user_id": "user_id",
        "transfer_to": "0xdef",
    }.get(k)
    mock_to_checksum.return_value = "0xdef"
    mock_account = MagicMock()
    mock_account.send_native.return_value = "0xhash"
    mock_wallet.from_user_id.return_value = mock_account
    result = native_transfer.handle_task(mock_task)
    assert result[0] == mock_task.complete.return_value or result == mock_task.complete.return_value

@patch("wallet.native_transfer.Wallet")
def test_native_transfer_missing_amount(mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {
        "chain_id": 261,
        "camunda_user_id": "user_id",
        "transfer_to": "0xdef",
    }.get(k)
    result = native_transfer.handle_task(mock_task)
    assert mock_task.bpmn_error.called

@patch("wallet.native_transfer.Wallet")
def test_native_transfer_missing_user(mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {
        "chain_id": 261,
        "transfer_amount": 1.0,
        "transfer_to": "0xdef",
    }.get(k)
    result = native_transfer.handle_task(mock_task)
    assert mock_task.bpmn_error.called

@patch("wallet.native_transfer.Wallet")
def test_native_transfer_wallet_not_found(mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {
        "chain_id": 261,
        "transfer_amount": 1.0,
        "camunda_user_id": "user_id",
        "transfer_to": "0xdef",
    }.get(k)
    mock_wallet.from_user_id.return_value = None
    result = native_transfer.handle_task(mock_task)
    assert mock_task.bpmn_error.called 