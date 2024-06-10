import logging

import requests
from camunda.external_task.external_task_worker import ExternalTaskWorker, ExternalTask

from config import (
    CAMUNDA_URL,
    CAMUNDA_CLIENT_CONFIG,
    TOPIC_NAME,
    API_URL,
    SYS_KEY,
    INVITES_LIMIT,
)


def handle_task(task: ExternalTask):
    variables = task.get_variables()
    token_id = variables.get("token_id")
    chain_id = variables.get("chain_id", 8453)
    if not token_id or not chain_id:
        return task.bpmn_error(
            error_code="MISSING_TOKEN_OR_CHAIN_ID",
            error_message="Token ID or Chain ID is missing",
            variables={"available_invites": 0},
        )
    invited_wallets = requests.get(
        f"{API_URL}/invites/chain/{chain_id}/token/{token_id}",
        headers={"X-SYS-KEY": SYS_KEY},
    )
    try:
        invited_wallets.raise_for_status()
    except Exception as e:
        logging.error(e)
        return task.bpmn_error(
            error_code="FAILED_TO_FETCH_INVITED_WALLETS",  # This should match the error code in your BPMN model
            error_message=str(e),
            variables={
                "available_invites": None
            },  # You must return variables listed in the output of external task
        )
    invited_wallets = invited_wallets.json()
    return task.complete({"available_invites": INVITES_LIMIT - len(invited_wallets)})


if __name__ == "__main__":
    ExternalTaskWorker(
        worker_id="check_invite_quote",
        base_url=CAMUNDA_URL,
        config=CAMUNDA_CLIENT_CONFIG,
    ).subscribe(TOPIC_NAME, handle_task)
