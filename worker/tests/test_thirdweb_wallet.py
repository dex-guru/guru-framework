import pytest
from unittest.mock import patch, MagicMock
from wallet.wallet_interfaces import ThirdWebWallet
import httpx

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdweb_wallet_create(mock_get_web3):
    wallet = ThirdWebWallet("0x0000000000000000000000000000000000000001", 261)
    wallet.client = MagicMock(spec=httpx.Client)
    wallet.client.post.return_value.json.return_value = {
        "result": {"status": "success", "walletAddress": "0x0000000000000000000000000000000000000001"}
    }
    # Simulate the create method
    with patch.object(ThirdWebWallet, 'client', wallet.client):
        result_wallet = ThirdWebWallet.create("user_id", 261)
        assert result_wallet.address == "0x0000000000000000000000000000000000000001"
        assert result_wallet.chain_id == 261
        assert result_wallet.camunda_user_id == "user_id"

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdweb_wallet_send_transaction(mock_get_web3):
    mock_w3 = MagicMock()
    mock_w3.eth.wait_for_transaction_receipt.return_value.status = 1
    mock_get_web3.return_value = mock_w3
    wallet = ThirdWebWallet("0x0000000000000000000000000000000000000001", 261)
    wallet.client = MagicMock()
    wallet.client.post.return_value.json.return_value = {"result": {"queueId": "qid"}}
    wallet._wait_tx_task_done = MagicMock(return_value="0xhash")
    tx = {"to": "0x0000000000000000000000000000000000000002", "value": 1000, "data": "0x"}
    tx_hash = wallet.send_transaction(tx)
    assert tx_hash == "0xhash"

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdweb_wallet_send_native(mock_get_web3):
    mock_w3 = MagicMock()
    mock_w3.eth.wait_for_transaction_receipt.return_value.status = 1
    mock_get_web3.return_value = mock_w3
    wallet = ThirdWebWallet("0x0000000000000000000000000000000000000001", 261)
    wallet.client = MagicMock()
    wallet.client.post.return_value.json.return_value = {"result": {"queueId": "qid"}}
    wallet._wait_tx_task_done = MagicMock(return_value="0xhash")
    tx_hash = wallet.send_native("0x0000000000000000000000000000000000000002", 1000)
    assert tx_hash == "0xhash"

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdweb_wallet_send_erc20(mock_get_web3):
    mock_w3 = MagicMock()
    mock_w3.eth.wait_for_transaction_receipt.return_value.status = 1
    mock_get_web3.return_value = mock_w3
    wallet = ThirdWebWallet("0x0000000000000000000000000000000000000001", 261)
    wallet.client = MagicMock()
    wallet.client.get.return_value.json.return_value = {"result": {"decimals": 18}}
    wallet.client.post.return_value.json.return_value = {"result": {"queueId": "qid"}}
    wallet._wait_tx_task_done = MagicMock(return_value="0xhash")
    tx_hash = wallet.send_erc20("0x0000000000000000000000000000000000000002", 1000, "0xtoken")
    assert tx_hash == "0xhash"

@patch("wallet.wallet_interfaces.requests.put")
def test_thirdweb_wallet_save(mock_put):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_put.return_value = mock_response
    wallet = ThirdWebWallet("0x0000000000000000000000000000000000000001", 261, "user_id")
    wallet.save()
    mock_put.assert_called_once()

def test_thirdweb_wallet_sign_transaction():
    wallet = ThirdWebWallet("0x0000000000000000000000000000000000000001", 261)
    wallet.client = MagicMock()
    wallet.client.post.return_value.json.return_value = {"result": "signed_tx"}
    tx = {"to": "0x0000000000000000000000000000000000000002", "value": 1000}
    signed = wallet.sign_transaction(tx)
    assert signed == "signed_tx"

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdweb_wallet_send_raw_transaction(mock_get_web3):
    mock_w3 = MagicMock()
    mock_w3.eth.send_raw_transaction.return_value = b"\x12"
    mock_w3.eth.wait_for_transaction_receipt.return_value = MagicMock(status=1)
    mock_get_web3.return_value = mock_w3
    wallet = ThirdWebWallet("0x0000000000000000000000000000000000000001", 261)
    tx_hash = wallet.send_raw_transaction(b"\x12")
    assert isinstance(tx_hash, str) 