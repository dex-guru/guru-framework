import os
import unittest
from unittest.mock import patch, MagicMock

from web3_workers import transaction_executing as te


class TestTransactionExecuting(unittest.TestCase):

    def setUp(self):
        os.environ["PRIVATE_KEY"] = (
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )
        os.environ["WEB3_URL"] = "http://rpc-gw-stage.dexguru.biz/full/1"

    @patch("external_workers.web3_workers.transaction_executing.get_quote")
    @patch("external_workers.web3_workers.transaction_executing.is_enough_allowance")
    @patch(
        "external_workers.web3_workers.transaction_executing.w3.eth.send_raw_transaction"
    )
    @patch(
        "external_workers.web3_workers.transaction_executing.w3.eth.wait_for_transaction_receipt"
    )
    def test_handle_task_buy_signal(
        self, mock_wait_receipt, mock_send_tx, mock_is_enough_allowance, mock_get_quote
    ):
        mock_wait_receipt.return_value = {"status": 1}
        mock_send_tx.return_value = "0x123"
        mock_get_quote.return_value = {
            "data": "0x123",
            "to": "0x0f3284bFEbc5f55B849c8CF792D39cC0f729e0BC",
            "value": 0,
            "gas": 100000,
            "gas_price": 65000000000,
        }
        mock_is_enough_allowance.return_value = True
        task = MagicMock()
        task.get_variables.return_value = {
            "trading_signal": "buy",
            "token_address": "0x0f3284bFEbc5f55B849c8CF792D39cC0f729e0BC",
            "is_backtesting": False,
        }
        result = te.handle_task(task)
        self.assertTrue(result)

    @patch("external_workers.web3_workers.transaction_executing.get_quote")
    @patch("external_workers.web3_workers.transaction_executing.is_enough_allowance")
    @patch(
        "external_workers.web3_workers.transaction_executing.w3.eth.send_raw_transaction"
    )
    @patch(
        "external_workers.web3_workers.transaction_executing.w3.eth.wait_for_transaction_receipt"
    )
    def test_handle_task_sell_signal(
        self, mock_wait_receipt, mock_send_tx, mock_is_enough_allowance, mock_get_quote
    ):
        mock_wait_receipt.return_value = {"status": 1}
        mock_send_tx.return_value = "0x123"
        mock_get_quote.return_value = {
            "data": "0x123",
            "to": "0x0f3284bFEbc5f55B849c8CF792D39cC0f729e0BC",
            "value": 0,
            "gas": 100000,
            "gas_price": 65000000000,
        }
        mock_is_enough_allowance.return_value = True
        task = MagicMock()
        task.get_variables.return_value = {
            "trading_signal": "sell",
            "token_address": "0x0f3284bFEbc5f55B849c8CF792D39cC0f729e0BC",
            "is_backtesting": False,
        }
        result = te.handle_task(task)
        self.assertTrue(result)

    @patch("external_workers.web3_workers.transaction_executing.requests.get")
    def test_get_quote_success(self, mock_get):
        mock_get.return_value.json.return_value = {"price": 1}
        result = te.get_quote("0x123", "0x456", 100)
        self.assertEqual(result, {"price": 1})

    @patch("external_workers.web3_workers.transaction_executing.requests.get")
    def test_get_quote_failure(self, mock_get):
        mock_get.return_value.json.return_value = {"error": "Unknown error"}
        with self.assertRaises(te.QuoteError):
            te.get_quote("0x123", "0x456", 100)

    @patch("external_workers.web3_workers.transaction_executing.w3.eth.contract")
    def test_is_enough_allowance_true(self, mock_contract):
        mock_contract.return_value.functions.allowance.return_value.call.return_value = (
            200
        )
        result = te.is_enough_allowance("0x123", "0x456", 100)
        self.assertTrue(result)

    @patch("external_workers.web3_workers.transaction_executing.w3.eth.contract")
    def test_is_enough_allowance_false(self, mock_contract):
        mock_contract.return_value.functions.allowance.return_value.call.return_value = (
            50
        )
        result = te.is_enough_allowance("0x123", "0x456", 100)
        self.assertFalse(result)


if __name__ == "__main__":

    unittest.main()
