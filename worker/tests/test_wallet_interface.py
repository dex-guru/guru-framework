import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from wallet.wallet_interfaces import Wallet, GuruWallet, ThirdWebWallet
from settings import worker
import types

@patch("wallet.wallet_interfaces.requests.get")
@patch("wallet.wallet_interfaces.fernet", return_value=MagicMock())
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_from_user_id_returns_guru_wallet(mock_get_w3, mock_fernet, mock_get):
    mock_get_w3.return_value = MagicMock()
    worker.worker_settings.INTERNAL_NETWORKS = [1]
    mock_response = MagicMock()
    mock_get.return_value = mock_response
    mock_response.ok = True
    mock_response.json.return_value = [
        {
            "network_type": "guru",
            "wallet_address": "0x0000000000000000000000000000000000000001",
            "private_key": "encrypted"
        }
    ]
    decrypt = mock_fernet.decrypt
    decrypt.return_value.decode.return_value = "0x1234567890123456789012345678901234567890123456789012345678901234"

    wallet = Wallet.from_user_id("user_id", "user_id", 1)
    assert isinstance(wallet, GuruWallet)
    assert wallet.address == "0x0000000000000000000000000000000000000001"

@patch("wallet.wallet_interfaces.requests.get")
def test_from_user_id_returns_none_for_invalid_user(mock_get):
    mock_get.return_value.ok = False
    with pytest.raises(ValueError):
        Wallet.from_user_id("invalid_user", "user_id", 1)

@patch("wallet.wallet_interfaces.requests.get")
def test_from_user_id_returns_none_for_no_wallets(mock_get):
    mock_get.return_value.json.return_value = []
    wallet = Wallet.from_user_id("user_id", "user_id", 1)
    assert wallet is None

@patch("wallet.wallet_interfaces.GuruWallet.create")
def test_create_returns_guru_wallet(mock_create):
    mock_create.return_value = MagicMock(spec=GuruWallet)
    wallet = Wallet.create("camunda_user_id", "guru", 1)
    assert isinstance(wallet, GuruWallet)

@patch("wallet.wallet_interfaces.ThirdWebWallet.create")
def test_create_returns_thirdweb_wallet(mock_create):
    mock_create.return_value = MagicMock(spec=ThirdWebWallet)
    wallet = Wallet.create("camunda_user_id", "thirdweb_ecosystem", 1)
    assert isinstance(wallet, ThirdWebWallet)

def test_create_raises_value_error_for_invalid_wallet_type():
    with pytest.raises(ValueError):
        Wallet.create("camunda_user_id", "invalid_type", 1)

# GuruWallet balance and nonce
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_guruwallet_balance_and_nonce(mock_get_w3):
    mock_w3 = MagicMock()
    mock_w3.eth.get_balance.return_value = 10**18
    mock_w3.eth.get_transaction_count.side_effect = lambda *args, **kwargs: 7
    mock_account = MagicMock()
    mock_w3.eth.account.from_key.return_value = mock_account
    mock_get_w3.return_value = mock_w3
    gw = GuruWallet("0x0000000000000000000000000000000000000001", "0x123", 1)
    assert gw.balance == 1.0
    assert gw.nonce == 1

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_guruwallet_balance_exception(mock_get_w3):
    mock_w3 = MagicMock()
    mock_w3.eth.get_balance.side_effect = Exception("web3 error")
    mock_get_w3.return_value = mock_w3
    gw = GuruWallet("0x0000000000000000000000000000000000000001", "0x123", 1)
    with pytest.raises(Exception):
        _ = gw.balance

# GuruWallet save
@patch("wallet.wallet_interfaces.fernet")
@patch("wallet.wallet_interfaces.requests.put")
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_guruwallet_save_http_error(mock_get_w3, mock_put, mock_fernet):
    mock_get_w3.return_value = MagicMock()
    mock_fernet.encrypt.return_value.decode.return_value = "enc"
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("HTTP error")
    mock_resp.text = "fail"
    mock_put.return_value = mock_resp
    gw = GuruWallet("0x0000000000000000000000000000000000000001", "0x123", 1)
    gw._GuruWallet__mnemonic = "mnemonic"
    with pytest.raises(Exception):
        gw.save()

# GuruWallet sign_transaction
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_guruwallet_sign_transaction(mock_get_w3):
    mock_w3 = MagicMock()
    mock_account = MagicMock()
    mock_account.sign_transaction.return_value.rawTransaction = b"signed"
    mock_w3.eth.account.from_key.return_value = mock_account
    mock_get_w3.return_value = mock_w3
    gw = GuruWallet("0x0000000000000000000000000000000000000001", "0x123", 1)
    gw.account = mock_account
    tx = {"to": "0x2", "value": 1}
    assert gw.sign_transaction(tx) == b"signed".hex()

# GuruWallet send_raw_transaction exception
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_guruwallet_send_raw_transaction_exception(mock_get_w3):
    mock_w3 = MagicMock()
    mock_w3.eth.send_raw_transaction.side_effect = Exception("send error")
    mock_get_w3.return_value = mock_w3
    gw = GuruWallet("0x0000000000000000000000000000000000000001", "0x123", 1)
    with pytest.raises(Exception):
        gw.send_raw_transaction(b"signed")

# ThirdWebWallet balance and nonce
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdwebwallet_balance_and_nonce(mock_get_w3):
    mock_w3 = MagicMock()
    mock_w3.eth.get_balance.return_value = 2 * 10**18
    mock_w3.eth.get_transaction_count.return_value = 3
    mock_get_w3.return_value = mock_w3
    tw = ThirdWebWallet("0x0000000000000000000000000000000000000002", 1)
    assert tw.balance == 2.0
    assert tw.nonce == 3

@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdwebwallet_balance_exception(mock_get_w3):
    mock_w3 = MagicMock()
    mock_w3.eth.get_balance.side_effect = Exception("web3 error")
    mock_get_w3.return_value = mock_w3
    tw = ThirdWebWallet("0x0000000000000000000000000000000000000002", 1)
    with pytest.raises(Exception):
        _ = tw.balance

# ThirdWebWallet save
@patch("wallet.wallet_interfaces.requests.put")
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdwebwallet_save_success(mock_get_w3, mock_put):
    mock_get_w3.return_value = MagicMock()
    mock_put.return_value.raise_for_status.return_value = None
    tw = ThirdWebWallet("0x0000000000000000000000000000000000000002", 1)
    tw.save()
    assert mock_put.called

@patch("wallet.wallet_interfaces.requests.put")
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdwebwallet_save_http_error(mock_get_w3, mock_put):
    mock_get_w3.return_value = MagicMock()
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("HTTP error")
    mock_resp.text = "fail"
    mock_put.return_value = mock_resp
    tw = ThirdWebWallet("0x0000000000000000000000000000000000000002", 1)
    with pytest.raises(Exception):
        tw.save()

# ThirdWebWallet sign_transaction
@patch("wallet.wallet_interfaces.ThirdWebWallet.client.post")
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdwebwallet_sign_transaction(mock_get_w3, mock_post):
    mock_get_w3.return_value = MagicMock()
    mock_post.return_value.raise_for_status.return_value = None
    mock_post.return_value.json.return_value = {"result": "signed_tx"}
    tw = ThirdWebWallet("0x0000000000000000000000000000000000000002", 1)
    tx = {"to": "0x2", "value": 1}
    assert tw.sign_transaction(tx) == "signed_tx"

# ThirdWebWallet send_raw_transaction exception
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_thirdwebwallet_send_raw_transaction_exception(mock_get_w3):
    mock_w3 = MagicMock()
    mock_w3.eth.send_raw_transaction.side_effect = Exception("send error")
    mock_get_w3.return_value = mock_w3
    tw = ThirdWebWallet("0x0000000000000000000000000000000000000002", 1)
    with pytest.raises(Exception):
        tw.send_raw_transaction(b"signed")

@pytest.fixture
def mock_account():
    account = MagicMock(spec=WalletI)
    account.address = "0x0000000000000000000000000000000000000002"
    return account
