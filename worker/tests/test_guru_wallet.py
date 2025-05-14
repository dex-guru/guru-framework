import pytest
from unittest.mock import patch, MagicMock
from wallet.wallet_interfaces import GuruWallet
import httpx

VALID_PRIV_KEY = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

@patch("wallet.wallet_interfaces.Account")
def test_guru_wallet_create(mock_account):
    mock_account.create_with_mnemonic.return_value = (
        MagicMock(key=b"\x12" * 32, address="0x0000000000000000000000000000000000000001"), "mnemonic"
    )
    mock_account.return_value = MagicMock()
    wallet = GuruWallet.create("user_id", 261)
    assert wallet.address == "0x0000000000000000000000000000000000000001"
    assert wallet._GuruWallet__mnemonic == "mnemonic"

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_guru_wallet_send_transaction(mock_get_web3):
    mock_w3 = MagicMock()
    mock_w3.eth.send_raw_transaction.return_value = b"\x12"
    mock_w3.eth.wait_for_transaction_receipt.return_value = MagicMock(status=1)
    mock_w3.eth.account.from_key.return_value.sign_transaction.return_value = MagicMock(rawTransaction=b"\x12")
    mock_get_web3.return_value = mock_w3
    wallet = GuruWallet("0x0000000000000000000000000000000000000001", VALID_PRIV_KEY, 261)
    wallet.account = MagicMock()
    wallet.account.sign_transaction.return_value = MagicMock(rawTransaction=b"\x12")
    tx = {"to": "0x0000000000000000000000000000000000000002", "value": 1000, "nonce": 1, "gas": 21000, "gasPrice": 100, "chainId": 261, "from": "0x0000000000000000000000000000000000000001"}
    tx_hash = wallet.send_transaction(tx)
    assert isinstance(tx_hash, str)

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_guru_wallet_send_native(mock_get_web3):
    mock_w3 = MagicMock()
    mock_w3.to_checksum_address.return_value = "0x0000000000000000000000000000000000000002"
    mock_w3.eth.gas_price = 100
    mock_w3.eth.account.from_key.return_value = MagicMock()
    mock_w3.eth.send_raw_transaction.return_value = b"\x12"
    mock_w3.eth.wait_for_transaction_receipt.return_value = MagicMock(status=1)
    mock_get_web3.return_value = mock_w3
    wallet = GuruWallet("0x0000000000000000000000000000000000000001", VALID_PRIV_KEY, 261)
    wallet.account = MagicMock()
    wallet.account.sign_transaction.return_value = MagicMock(rawTransaction=b"\x12")
    type(wallet).nonce = property(lambda self: 1)
    tx_hash = wallet.send_native("0x0000000000000000000000000000000000000002", 1000)
    assert isinstance(tx_hash, str)

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_guru_wallet_send_erc20(mock_get_web3):
    mock_w3 = MagicMock()
    mock_w3.eth.gas_price = 100
    mock_w3.eth.contract.return_value.functions.transfer.return_value.estimate_gas.return_value = 21000
    mock_w3.eth.send_raw_transaction.return_value = b"\x12"
    mock_w3.eth.wait_for_transaction_receipt.return_value = MagicMock(status=1)
    mock_get_web3.return_value = mock_w3
    wallet = GuruWallet("0x0000000000000000000000000000000000000001", VALID_PRIV_KEY, 261)
    wallet.account = MagicMock()
    wallet.account.sign_transaction.return_value = MagicMock(rawTransaction=b"\x12")
    type(wallet).nonce = property(lambda self: 1)
    tx_hash = wallet.send_erc20("0x0000000000000000000000000000000000000002", 1000, "0x000000000000000000000000000000000000dead")
    assert isinstance(tx_hash, str)

@patch("wallet.wallet_interfaces.fernet")
@patch("wallet.wallet_interfaces.requests.put")
def test_guru_wallet_save(mock_put, mock_fernet):
    mock_fernet.encrypt.return_value.decode.return_value = "encrypted"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_put.return_value = mock_response
    wallet = GuruWallet("0x0000000000000000000000000000000000000001", VALID_PRIV_KEY, 261, "user_id", "mnemonic")
    wallet.save()
    mock_put.assert_called_once()

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_guru_wallet_sign_transaction(mock_get_web3):
    mock_w3 = MagicMock()
    mock_get_web3.return_value = mock_w3
    wallet = GuruWallet("0x0000000000000000000000000000000000000001", VALID_PRIV_KEY, 261)
    wallet.account = MagicMock()
    wallet.account.sign_transaction.return_value = MagicMock(rawTransaction=b"\x12")
    tx = {"to": "0x0000000000000000000000000000000000000002", "value": 1000}
    signed = wallet.sign_transaction(tx)
    assert isinstance(signed, str)

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_guru_wallet_send_raw_transaction(mock_get_web3):
    mock_w3 = MagicMock()
    mock_w3.eth.send_raw_transaction.return_value = b"\x12"
    mock_w3.eth.wait_for_transaction_receipt.return_value = MagicMock(status=1)
    mock_get_web3.return_value = mock_w3
    wallet = GuruWallet("0x0000000000000000000000000000000000000001", VALID_PRIV_KEY, 261)
    tx_hash = wallet.send_raw_transaction(b"\x12")
    assert isinstance(tx_hash, str) 