import logging

from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from testnet_arbitrage.execute_swap import get_pool_contract, get_pool_tokens, get_token_decimals, get_pool_reserves
from web3 import Web3

from config import (
    WEB3_URL,
    CAMUNDA_URL,
    CAMUNDA_CLIENT_CONFIG,
    TOPIC_NAME
)

logger = logging.getLogger(__name__)

w3 = Web3(Web3.HTTPProvider(WEB3_URL))


def handle_task(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()

    target_pool_address = variables.get("pool_address")
    target_token_address = variables.get("token_address")

    try:
        target_pool_address = w3.to_checksum_address(target_pool_address)
        target_token_address = w3.to_checksum_address(target_token_address)
        pool_contract = get_pool_contract(target_pool_address)
        pool_tokens = get_pool_tokens(pool_contract)
        if target_token_address == pool_tokens[0]:
            target_token_index = 0
        elif target_token_address == pool_tokens[1]:
            target_token_index = 1
        else:
            raise ValueError("Token not in pool")

        decimals = [get_token_decimals(pool_tokens[0]), get_token_decimals(pool_tokens[1])]
        reserves = get_pool_reserves(pool_contract, target_token_address)
        current_price = (
            reserves.other_token_reserve / 10 ** decimals[1 - target_token_index]
        ) / (reserves.target_token_reserve / 10 ** decimals[target_token_index])

        variables['current_price'] = current_price
        logger.info(f'''Success calculated price from pool - {target_token_address} 
                        for token - {target_pool_address}''')
        return task.complete(variables)
    except Exception as e:
        logger.error(e)
        return task.failure(f'''Cannot get token price from pool - {target_token_address} 
                         for token - {target_pool_address}''',
                     'Cannot resolve token price from pool',
                     max_retries=3,
                     retry_timeout=15000)


if __name__ == "__main__":
    ExternalTaskWorker(
        worker_id="1", base_url=CAMUNDA_URL, config=CAMUNDA_CLIENT_CONFIG
    ).subscribe([TOPIC_NAME], handle_task)
