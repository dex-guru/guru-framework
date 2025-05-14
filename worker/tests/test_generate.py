import pytest
from unittest.mock import patch, MagicMock
from wallet import generate

@patch("wallet.generate.Wallet")
@patch("wallet.generate.settings")
def test_generate_success(mock_settings, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {"camunda_user_id": "user1", "ref_user_id": None}.get(k)
    mock_wallet.from_user_id.return_value = None
    mock_account = MagicMock()
    mock_account.address = "0x0000000000000000000000000000000000000001"
    mock_wallet.create.return_value = mock_account
    result = generate.handle_task(mock_task)
    assert result[0] == mock_task.complete.return_value or result == mock_task.complete.return_value

@patch("wallet.generate.Wallet")
@patch("wallet.generate.settings")
def test_generate_user_exists(mock_settings, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {"camunda_user_id": "user1", "ref_user_id": None}.get(k)
    mock_account = MagicMock()
    mock_account.address = "0x0000000000000000000000000000000000000001"
    mock_wallet.from_user_id.return_value = mock_account
    result = generate.handle_task(mock_task)
    assert result[0] == mock_task.bpmn_error.return_value or result == mock_task.bpmn_error.return_value

@patch("wallet.generate.Wallet")
@patch("wallet.generate.settings")
def test_generate_with_ref_user(mock_settings, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {"camunda_user_id": "user1", "ref_user_id": "refuser"}.get(k)
    mock_wallet.from_user_id.side_effect = [None, MagicMock(address="0x0000000000000000000000000000000000000002")]
    mock_account = MagicMock()
    mock_account.address = "0x0000000000000000000000000000000000000001"
    mock_wallet.create.return_value = mock_account
    result = generate.handle_task(mock_task)
    assert result[0] == mock_task.complete.return_value or result == mock_task.complete.return_value

@patch("wallet.generate.Wallet")
@patch("wallet.generate.settings")
def test_generate_save_fails(mock_settings, mock_wallet):
    mock_task = MagicMock()
    mock_task.get_variable.side_effect = lambda k: {"camunda_user_id": "user1", "ref_user_id": None}.get(k)
    mock_wallet.from_user_id.return_value = None
    mock_account = MagicMock()
    mock_account.address = "0x0000000000000000000000000000000000000001"
    mock_account.save.side_effect = Exception("fail")
    mock_wallet.create.return_value = mock_account
    result = generate.handle_task(mock_task)
    assert result[0] == mock_task.failure.return_value or result == mock_task.failure.return_value 