from datetime import datetime, timedelta

import logging

import requests
from camunda.external_task.external_task_worker import ExternalTaskWorker, ExternalTask

from config import (
    CAMUNDA_URL,
    CAMUNDA_CLIENT_CONFIG,
    API_URL,
    SYS_KEY,
)


def handle_task(task: ExternalTask):
    variables = task.get_variables()
    token_id = variables.get("token_id")
    chain_id = variables.get("chain_id", 8453)
    wallet = variables.get(f"wallet_1")
    if not wallet:
        return task.bpmn_error(
            error_code="MISSING_WALLET",
            error_message="Wallet is missing",
            variables={"next_invite_date_iso": None},
        )
    resp = requests.post(
        f"{API_URL}/invites/chain/{chain_id}/token/{token_id}",
        headers={"X-SYS-KEY": SYS_KEY},
        json=wallet,
    )
    try:
        resp.raise_for_status()
    except Exception as e:
        logging.error(e)
        return task.bpmn_error(
            error_code="FAILED_TO_UPDATE_INVITED_WALLETS",
            error_message=str(e),
            variables={"next_invite_date_iso": None},
        )

    # Calculate next invite date
    next_invite_date = datetime.utcnow() + timedelta(hours=24)
    next_invite_date_iso = (
        next_invite_date.isoformat() + "Z"
    )  # Ensure it's in UTC and ISO8601 format

    return task.complete(
        {
            "next_invite_date_iso": next_invite_date_iso,
            "invite_hash": resp.json().get("id"),
            "activation_ts": next_invite_date.timestamp(),
        }
    )


if __name__ == "__main__":
    ExternalTaskWorker(
        worker_id="write_invited_wallets_in_db",
        base_url=CAMUNDA_URL,
        config=CAMUNDA_CLIENT_CONFIG,
    ).subscribe(['writeInvitedWallets'], handle_task)
