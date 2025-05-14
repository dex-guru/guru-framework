import pytest
from unittest.mock import patch, MagicMock
from wallet.wallet_interfaces import Wallet, GuruWallet, ThirdWebWallet

VALID_PRIV_KEY = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
VALID_ADDRESS_1 = "0x0000000000000000000000000000000000000001"
VALID_ADDRESS_2 = "0x0000000000000000000000000000000000000002"

@patch("wallet.wallet_interfaces.requests.get")
@patch("wallet.wallet_interfaces.fernet")
def test_wallet_from_user_id_guru(mock_fernet, mock_get):
    mock_get.return_value.ok = True
    mock_get.return_value.json.return_value = [
        {"network_type": "guru", "wallet_address": VALID_ADDRESS_1, "private_key": "encrypted"}
    ]
    mock_fernet.decrypt.return_value.decode.return_value = VALID_PRIV_KEY
    wallet = Wallet.from_user_id("user_id", "user_id", 261)
    assert isinstance(wallet, GuruWallet)
    assert wallet.address == VALID_ADDRESS_1

@patch("wallet.wallet_interfaces.requests.get")
@patch("wallet.wallet_interfaces.get_web3_client_by_chain_id")
def test_wallet_from_user_id_thirdweb(mock_get_w3, mock_get):
    mock_get_w3.return_value = MagicMock()
    mock_get.return_value.ok = True
    mock_get.return_value.json.return_value = [
        {"network_type": "thirdweb_ecosystem", "wallet_address": VALID_ADDRESS_2}
    ]
    wallet = Wallet.from_user_id("user_id", "user_id", 9999)
    assert isinstance(wallet, ThirdWebWallet)
    assert wallet.address == VALID_ADDRESS_2

@patch("wallet.wallet_interfaces.requests.get")
def test_wallet_from_user_id_error(mock_get):
    mock_get.return_value.ok = False
    with pytest.raises(ValueError):
        Wallet.from_user_id("bad_user", "user_id", 261)

@patch("wallet.wallet_interfaces.requests.get")
def test_wallet_from_user_id_no_wallets(mock_get):
    mock_get.return_value.ok = True
    mock_get.return_value.json.return_value = []
    wallet = Wallet.from_user_id("user_id", "user_id", 261)
    assert wallet is None

@patch("wallet.wallet_interfaces.GuruWallet.create")
def test_wallet_create_guru(mock_create):
    mock_create.return_value = MagicMock(spec=GuruWallet)
    wallet = Wallet.create("user_id", "guru", 261)
    assert isinstance(wallet, GuruWallet)

@patch("wallet.wallet_interfaces.ThirdWebWallet.create")
def test_wallet_create_thirdweb(mock_create):
    mock_create.return_value = MagicMock(spec=ThirdWebWallet)
    wallet = Wallet.create("user_id", "thirdweb_ecosystem", 261)
    assert isinstance(wallet, ThirdWebWallet)

def test_wallet_create_invalid_type():
    with pytest.raises(ValueError):
        Wallet.create("user_id", "invalid_type", 261)

@patch("wallet.wallet_interfaces.Account.from_key")
def test_wallet_from_key(mock_from_key):
    mock_from_key.return_value.address = VALID_ADDRESS_1
    wallet = Wallet.from_key(VALID_PRIV_KEY, 261)
    assert isinstance(wallet, GuruWallet)
    assert wallet.address == VALID_ADDRESS_1 