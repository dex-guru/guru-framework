import logging
import time
from typing import Literal, Union, Protocol

import requests
from cryptography.fernet import Fernet
from eth_account import Account
from eth_typing import HexStr, ChecksumAddress
from eth_utils import to_checksum_address
from web3.exceptions import TimeExhausted

from common.utils import get_web3_client_by_chain_id
from settings.worker import worker_settings

GURU_WALLET_TYPE = "guru"
THIRDWEB_WALLET_TYPE = "thirdweb_ecosystem"

try:
    # Initialize the Fernet cipher for required workers
    fernet = Fernet(worker_settings.CRYPTO_KEY.encode())
except Exception as e:
    fernet = None

logger = logging.getLogger(__name__)


class WalletI(Protocol):
    address: str | ChecksumAddress
    chain_id: int | None
    camunda_user_id: str | None

    @property
    def balance(self) -> float:
        pass

    @property
    def nonce(self) -> int:
        pass

    def send_transaction(self, tx: dict) -> [HexStr, str]:
        pass

    def sign_transaction(self, tx: dict) -> str:
        pass

    def send_native(self, to: str, amount: int) -> str:
        pass

    def send_erc20(self, to: str, amount_wei: int, token_address: str) -> str:
        pass

    def create(self, camunda_user_id: str, chain_id: int | None = None) -> "WalletI":
        pass

    def save(self):
        pass

    def send_raw_transaction(self, signed_tx: HexStr | bytes) -> HexStr:
        pass


class Wallet:

    @classmethod
    def from_user_id(
        cls,
        user_id: str,
        id_type: Literal[
            "user_id", "camunda_user_id", "telegram_user_id", "webapp_user_id"
        ],
        chain_id: int,
        wallet_type: str | None = None,
    ) -> Union[WalletI, None]:
        response = requests.get(
            f"{worker_settings.FLOW_API_URL}/api/wallets",
            params={id_type: user_id},
            headers={"X-SYS-KEY": worker_settings.FLOW_API_SYS_KEY},
        )
        if not response.ok:
            raise ValueError(f"Failed to get wallet for user {user_id}")
        data = response.json()
        chain_id = int(chain_id)
        desired_type = wallet_type or (
            GURU_WALLET_TYPE
            if chain_id in worker_settings.INTERNAL_NETWORKS
            else THIRDWEB_WALLET_TYPE
        )
        for wallet in data:
            address_type = wallet.get("network_type")
            if address_type == desired_type:
                if address_type == GURU_WALLET_TYPE:
                    pk = fernet.decrypt(wallet.get("private_key").encode()).decode()
                    return GuruWallet(wallet.get("wallet_address"), pk, chain_id)
                elif address_type == THIRDWEB_WALLET_TYPE:
                    return ThirdWebWallet(wallet.get("wallet_address"), chain_id)
        return None

    @classmethod
    def create(
        cls,
        camunda_user_id: str,
        wallet_type: Literal["guru", "thirdweb_ecosystem"],
        chain_id: int | None = None,
    ) -> WalletI:
        logger.info("Generating wallet...")
        if wallet_type == GURU_WALLET_TYPE:
            return GuruWallet.create(camunda_user_id, chain_id)
        if wallet_type == THIRDWEB_WALLET_TYPE:
            return ThirdWebWallet.create(camunda_user_id, chain_id)
        raise ValueError(f"Invalid wallet type: {wallet_type}")

    @classmethod
    def from_key(cls, private_key: str, chain_id: int = None) -> WalletI:
        account = Account.from_key(private_key)
        address = account.address
        return GuruWallet(address, private_key, chain_id)


class GuruWallet:

    def __init__(
        self,
        address: str,
        private_key: str,
        chain_id: int,
        camunda_user_id: str | None = None,
        mnemonic: str | None = None,
    ):
        self.address = to_checksum_address(address)
        self.chain_id = chain_id
        self.camunda_user_id = camunda_user_id
        self.w3 = get_web3_client_by_chain_id(chain_id)
        self.account = self.w3.eth.account.from_key(private_key)

        self.__private_key = private_key
        self.__mnemonic = mnemonic

    @property
    def balance(self) -> float:
        return self.w3.eth.get_balance(self.address) / 10**18

    @property
    def nonce(self) -> int:
        return self.w3.eth.get_transaction_count(self.address)

    @classmethod
    def create(cls, camunda_user_id: str, chain_id: int | None = None) -> WalletI:
        logger.info("Generating wallet...")
        account = Account()
        account.enable_unaudited_hdwallet_features()
        account, mnemonic = Account.create_with_mnemonic()
        pk = account.key.hex()
        address = account.address
        return cls(address, pk, chain_id, camunda_user_id, mnemonic)

    def send_transaction(self, tx: dict) -> [HexStr, str]:
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        retries = 0
        while retries < 5:
            try:
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=40)
                break
            except TimeExhausted:
                retries += 1
                if tx.get("maxFeePerGas"):
                    tx["maxFeePerGas"] = int(tx["maxFeePerGas"] * 1.2)
                else:
                    tx["gasPrice"] = int(tx["gasPrice"] * 1.2)
                continue

        return tx_hash.hex()

    def send_raw_transaction(self, signed_tx: HexStr | bytes) -> [HexStr, str]:
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx)
        retries = 0
        while retries < 5:
            try:
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=40)
                break
            except TimeExhausted:
                retries += 1
                continue
        return tx_hash.hex()

    def sign_transaction(self, tx: dict) -> HexStr:
        signed_tx = self.account.sign_transaction(tx)
        return signed_tx.rawTransaction.hex()

    def send_native(self, to: str, amount: int) -> [HexStr, str]:
        # Fetch the current gas price or use recommended EIP-1559 fields
        tx = {
            "to": self.w3.to_checksum_address(to),
            "from": self.address,
            "value": amount,
            "nonce": self.nonce,
            "gas": worker_settings.NATIVE_SEND_GAS_LIMIT,
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.chain_id,
        }
        return self.send_transaction(tx)

    def save(self):
        encoded_pk = fernet.encrypt(self.__private_key.encode()).decode()
        mnemonic = fernet.encrypt(self.__mnemonic.encode()).decode()
        response = requests.put(
            f"{worker_settings.FLOW_API_URL}/api/users",
            json={
                "wallet_address": self.address,
                "private_key": encoded_pk,
                "camunda_user_id": self.camunda_user_id,
                "mnemonic": mnemonic,
                "network_type": "guru",
            },
            headers={"X-SYS-KEY": worker_settings.FLOW_API_SYS_KEY},
        )
        try:
            response.raise_for_status()
        except requests.HTTPError:
            raise Exception(response.text)

    def send_erc20(self, to: str, amount_wei: int, token_address: str) -> [HexStr, str]:
        # Fetch the current gas price or use recommended EIP-1559 fields
        erc20_transfer_method_id = "0xa9059cbb"  # transfer(address,uint256)
        recipient_clean = to.lower().replace("0x", "").zfill(64)
        amount_hex = hex(int(amount_wei))[2:].zfill(64)

        data = erc20_transfer_method_id + recipient_clean + amount_hex
        tx = {
            "to": to_checksum_address(token_address),
            "from": self.address,
            "value": 0,
            "data": data,
            "nonce": self.nonce,
            "chainId": self.chain_id,
        }
        gas = self.w3.eth.estimate_gas(tx) + 5000
        tx["gas"] = gas
        tx["gasPrice"] = self.w3.eth.gas_price + 2 * 10**9  # 1 Gwei
        return self.send_transaction(tx)


class ThirdWebWallet:
    import httpx

    THIRDWEB_ENGINE_URL = worker_settings.THIRDWEB_ENGINE_URL
    THIRDWEB_ACCESS_KEY = f"Bearer {worker_settings.THIRDWEB_ACCESS_KEY}"
    client = httpx.Client(
        base_url=THIRDWEB_ENGINE_URL,
        headers={
            "Authorization": THIRDWEB_ACCESS_KEY,
            "Content-Type": "application/json",
        },
    )

    def __init__(self, address: str, chain_id: int, camunda_user_id: str = None):
        self.address = to_checksum_address(address)
        self.chain_id = chain_id
        self.camunda_user_id = camunda_user_id
        self.w3 = get_web3_client_by_chain_id(chain_id)

    def _wait_tx_task_done(self, queue_id: str, retries: int = 60) -> [str, None]:
        tx_hash = None
        while retries:
            resp = self.client.get(f"transaction/status/{queue_id}")
            retries -= 1
            resp.raise_for_status()
            data = resp.json()
            if data["result"]["status"] == "errored":
                raise Exception(data["result"]["errorMessage"])
            if data["result"]["transactionHash"] is not None:
                tx_hash = data["result"]["transactionHash"]
                return tx_hash
            else:
                time.sleep(2)
        if not tx_hash:
            # TODO cancel transaction
            raise TimeExhausted("Transaction timed out")
        return tx_hash

    @staticmethod
    def _convert_web3_tx_to_thirdweb(tx: dict) -> dict:
        thirdweb_tx = {}
        # override_keys = ["gas", "gasPrice", "maxFeePerGas", "maxPriorityFeePerGas"]
        thirdweb_tx["toAddress"] = str(tx["to"])
        thirdweb_tx["value"] = hex(tx["value"])
        thirdweb_tx["data"] = str(tx["data"])
        # overrides = {}
        # for k, v in tx.items():
        #     if k in override_keys:
        #         overrides[k] = str(v)
        #
        # thirdweb_tx["txOverrides"] = overrides
        return thirdweb_tx

    def _cancel_tx(self, tx: dict): ...

    def send_transaction(self, tx: dict) -> HexStr:
        tw_tx = self._convert_web3_tx_to_thirdweb(tx)
        # if not tw_tx["txOverrides"]:
        #     tw_tx.pop("txOverrides")
        resp = self.client.post(
            f"backend-wallet/{self.chain_id}/send-transaction",
            json=tw_tx,
            headers={
                "X-Backend-Wallet-Address": worker_settings.THIRDWEB_BACKEND_WALLET,
                "X-Account-Address": self.address,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        queue_id = data["result"]["queueId"]
        tx_hash = self._wait_tx_task_done(queue_id)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise Exception("Transaction failed")
        return tx_hash

    def send_raw_transaction(self, signed_tx: HexStr | bytes) -> [HexStr, str]:
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx)
        retries = 0
        while retries < 5:
            try:
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=40)
                break
            except TimeExhausted:
                retries += 1
                continue
        return tx_hash.hex()

    def sign_transaction(self, tx: dict) -> HexStr:
        resp = self.client.post(
            "backend-wallet/sign-transaction",
            json={"transaction": tx},
            headers={"X-Backend-Wallet-Address": self.address},
        )
        resp.raise_for_status()
        data = resp.json()
        signed_tx = data["result"]
        return signed_tx

    def send_native(self, to: str, amount: int) -> HexStr:

        tx = {
            "to": to,
            "value": amount,
            "data": "0x",
        }
        return self.send_transaction(tx)

    @property
    def balance(self) -> float:
        return self.w3.eth.get_balance(self.address) / 10**18

    @property
    def nonce(self) -> int:
        return self.w3.eth.get_transaction_count(self.address)

    @classmethod
    def create(cls, camunda_user_id: str, chain_id: int | None = None) -> WalletI:
        resp = cls.client.post("backend-wallet/create", json={})
        resp.raise_for_status()
        data = resp.json()
        if data["result"]["status"] != "success":
            raise Exception(data["result"]["message"])
        wallet_address = data["result"]["walletAddress"]
        return cls(wallet_address, chain_id, camunda_user_id)

    def save(self):
        response = requests.put(
            f"{worker_settings.FLOW_API_URL}/api/users",
            json={
                "wallet_address": self.address,
                "camunda_user_id": self.camunda_user_id,
                "network_type": THIRDWEB_WALLET_TYPE,
            },
            headers={"X-SYS-KEY": worker_settings.FLOW_API_SYS_KEY},
        )
        try:
            response.raise_for_status()
        except requests.HTTPError:
            raise Exception(response.text)

    def send_erc20(self, to: str, amount_wei: int, token_address: str) -> [HexStr, str]:
        resp = self.client.get(f"/contract/{self.chain_id}/{token_address}/erc20/get")
        resp.raise_for_status()
        data = resp.json()
        decimals = int(data["result"]["decimals"])
        amount = int(amount_wei * 10**decimals)

        resp = self.client.post(
            f"/contract/{self.chain_id}/{token_address}/erc20/transfer-from",
            json={
                "fromAddress": self.address,
                "toAddress": to,
                "amount": amount,
            },
            headers={
                "X-Backend-Wallet-Address": worker_settings.THIRDWEB_BACKEND_WALLET,
                "X-Account-Address": self.address,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        queue_id = data["result"]["queueId"]
        tx_hash = self._wait_tx_task_done(queue_id)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise Exception("Transaction failed")
        return tx_hash
