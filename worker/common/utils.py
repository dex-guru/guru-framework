import uuid
import logging

import boto3
import requests

from typing import Callable, Tuple, Iterable

from botocore.exceptions import NoCredentialsError
from camunda.external_task.external_task_worker import ExternalTaskWorker

from web3 import HTTPProvider, Web3

from settings.worker import worker_settings as settings

logging.basicConfig(
    level=settings.LOGGING_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def setup_worker(topic: str | Iterable[str], handle_task: Callable):
    if isinstance(topic, str):
        topic = [topic]
    worker_id = f"{topic[0]}_{uuid.uuid4().hex[:8]}"

    WORKER_CONFIG: dict = {
        "auth_basic": {
            "username": settings.ENGINE_USERNAME,
            "password": settings.ENGINE_PASSWORD,
        },
        "maxTasks": 1,
        "lockDuration": settings.WORKER_LOCK_DURATION,
        "asyncResponseTimeout": 5000,
        "retries": settings.WORKER_RETRIES,
        "retryTimeout": 15000,
        "sleepSeconds": 10,
    }

    ExternalTaskWorker(
        worker_id=worker_id,
        base_url=settings.ENGINE_URL,
        config=WORKER_CONFIG,
    ).subscribe(topic, handle_task)


def get_telegram_info(camunda_user_id: int) -> Tuple[int, bool]:
    headers = {
        "Content-Type": "application/json",
        "X-SYS-KEY": settings.FLOW_API_SYS_KEY,
    }

    try:
        response = requests.get(
            f"{settings.FLOW_API_URL}/api/users?camunda_user_id={camunda_user_id}",
            headers=headers,
        )
        response.raise_for_status()

        user = response.json()
        telegram_user_id = user.get("telegram_user_id")
        is_premium = user.get("is_premium")
        return telegram_user_id, is_premium

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get User Info. Exception: {e}")
        raise e  # R


def upload_file_to_s3_binary(content: bytes, s3_file_name) -> str:
    """
    Uploads binary content to AWS S3 and returns the file URL.

    Parameters:
    - content: Binary content of the file to upload.
    - bucket_name: Name of the S3 bucket.
    - s3_file_name: Object name in S3.

    Returns:
    - URL of the uploaded file on success.
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION_NAME,
    )
    try:
        s3.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME, Key=s3_file_name, Body=content
        )
        # location = s3.get_bucket_location(Bucket=AWS_S3_BUCKET_NAME)['LocationConstraint']
        url = f"https://img.burning.meme/{s3_file_name}"
        return url
    except NoCredentialsError:
        print("Credentials not available")
        return None


def get_web3_client_by_chain_id(chain_id: int) -> Web3:
    if not chain_id:
        url = settings.RPC_URL
    elif chain_id == 261:
        url = "https://rpc-test.gurunetwork.ai"
    elif chain_id == 8453:
        url = "https://base-rpc.publicnode.com"
    elif chain_id == 260:
        url = "https://rpc-guru-2k3v53llpe.t.conduit.xyz"
    elif chain_id == 84532:
        url = "https://base-sepolia.drpc.org"
    else:
        raise ValueError(f"Unsupported chain ID: {chain_id}")
    w3 = Web3(HTTPProvider(url))
    return w3
