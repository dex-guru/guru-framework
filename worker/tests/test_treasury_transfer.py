import pytest
from unittest.mock import patch, MagicMock
from wallet import treasury_transfer

@patch("wallet.treasury_transfer.Wallet")
@patch("wallet.treasury_transfer.settings")
def test_treasury_transfer_native_positive(mock_settings, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {
        "chain_id": 261,
        "transfer_amount": 1.0,
        "camunda_user_id": "user_id",
    }.get(k)
    mock_task.get_topic_name.return_value = "wallet_treasury_transfer"
    treasury_wallet = MagicMock()
    user_wallet = MagicMock()
    treasury_wallet.send_native.return_value = "0xhash"
    mock_wallet.from_key.return_value = treasury_wallet
    mock_wallet.from_user_id.return_value = user_wallet
    result = treasury_transfer.handle_task(mock_task)
    assert result[0] == mock_task.complete.return_value or result == mock_task.complete.return_value

@patch("wallet.treasury_transfer.Wallet")
@patch("wallet.treasury_transfer.settings")
def test_treasury_transfer_native_negative(mock_settings, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {
        "chain_id": 261,
        "transfer_amount": -1.0,
        "camunda_user_id": "user_id",
    }.get(k)
    mock_task.get_topic_name.return_value = "wallet_treasury_transfer"
    treasury_wallet = MagicMock()
    user_wallet = MagicMock()
    user_wallet.send_native.return_value = "0xhash"
    mock_wallet.from_key.return_value = treasury_wallet
    mock_wallet.from_user_id.return_value = user_wallet
    result = treasury_transfer.handle_task(mock_task)
    assert result[0] == mock_task.complete.return_value or result == mock_task.complete.return_value

@patch("wallet.treasury_transfer.Wallet")
@patch("wallet.treasury_transfer.settings")
def test_treasury_transfer_erc20_positive(mock_settings, mock_wallet):
    import wallet.treasury_transfer
    wallet.treasury_transfer.CHAIN_ID_TO_GURU_ADDRESS[261] = "0x000000000000000000000000000000000000dead"
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {
        "chain_id": 261,
        "transfer_amount": 1.0,
        "camunda_user_id": "user_id",
    }.get(k)
    mock_task.get_topic_name.return_value = "erc20_treasury_transfer"
    treasury_wallet = MagicMock()
    user_wallet = MagicMock()
    user_wallet.chain_id = 261
    user_wallet.address = "0x0000000000000000000000000000000000000002"
    treasury_wallet.send_erc20.return_value = "0xhash"
    mock_wallet.from_key.return_value = treasury_wallet
    mock_wallet.from_user_id.return_value = user_wallet
    result = treasury_transfer.handle_task(mock_task)
    assert result[0] == mock_task.complete.return_value or result == mock_task.complete.return_value

@patch("wallet.treasury_transfer.Wallet")
@patch("wallet.treasury_transfer.settings")
def test_treasury_transfer_erc20_negative(mock_settings, mock_wallet):
    import wallet.treasury_transfer
    wallet.treasury_transfer.CHAIN_ID_TO_GURU_ADDRESS[261] = "0x000000000000000000000000000000000000dead"
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {
        "chain_id": 261,
        "transfer_amount": -1.0,
        "camunda_user_id": "user_id",
    }.get(k)
    mock_task.get_topic_name.return_value = "erc20_treasury_transfer"
    treasury_wallet = MagicMock()
    user_wallet = MagicMock()
    user_wallet.chain_id = 261
    user_wallet.address = "0x0000000000000000000000000000000000000002"
    user_wallet.send_erc20.return_value = "0xhash"
    mock_wallet.from_key.return_value = treasury_wallet
    mock_wallet.from_user_id.return_value = user_wallet
    result = treasury_transfer.handle_task(mock_task)
    assert result[0] == mock_task.complete.return_value or result == mock_task.complete.return_value

@patch("wallet.treasury_transfer.Wallet")
@patch("wallet.treasury_transfer.settings")
def test_treasury_transfer_wallet_not_found(mock_settings, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {
        "chain_id": 261,
        "transfer_amount": 1.0,
        "camunda_user_id": "user_id",
    }.get(k)
    mock_task.get_topic_name.return_value = "wallet_treasury_transfer"
    mock_wallet.from_user_id.return_value = None
    result = treasury_transfer.handle_task(mock_task)
    assert mock_task.bpmn_error.called 