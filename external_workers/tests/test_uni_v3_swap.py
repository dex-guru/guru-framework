from unittest.mock import MagicMock
from external_workers.testnet_arbitrage.uniswap_v3_execue_swap import handle_task

vars = dict(
    rpc_url='https://glq-dataseed.graphlinq.io',
    uniswap_v3_router_address='0x47ab4f709b5c250026c4da83cde56fc2c81a311c',
    token_in='0xeb567ec41738c2bab2599a1070fc5b727721b3b6',
    token_out='0xbeed106d0f2e6950bfa1eec74e1253ca0a643442',
    amount_in=100,
    chain_id=614,
)


def test_handle_task():
    task_mock = MagicMock()
    task_mock.get_variables.return_value = vars
    # debug test
    # handle_task(task_mock)
