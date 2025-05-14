from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    pass

DIR = Path(__file__).absolute().parent.parent.parent
WORKER_DIR = Path(__file__).absolute().parent.parent

load_dotenv()


class EnvBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class WorkerSettings(EnvBaseSettings):
    ENVIRONMENT: str = "stage"
    ENGINE_URL: str = "http://localhost:8080/engine-rest"
    ENGINE_USERNAME: str = "demo"
    ENGINE_PASSWORD: str = "demo"
    WORKER_LOCK_DURATION: int = 10000
    WORKER_RETRIES: int = 3
    WORKER_TOPIC_NAME: str = "sendTelegramMessage"
    WORKER_TEST: bool = False
    WORKER_MAX_TASKS: int = 1

    WORKER_CONFIG: dict = {
        "auth_basic": {"username": ENGINE_USERNAME, "password": ENGINE_PASSWORD},
        "maxTasks": WORKER_MAX_TASKS,
        "lockDuration": WORKER_LOCK_DURATION,
        "asyncResponseTimeout": 5000,
        "retries": WORKER_RETRIES,
        "retryTimeout": 15000,
        "sleepSeconds": 10,
    }


# API Configuration
class APISettings(EnvBaseSettings):
    FLOW_API_URL: str = "http://localhost:8000"
    FLOW_API_SYS_KEY: str = "secret"


# Web3 Configuration
class Web3Settings(EnvBaseSettings):
    RPC_URL: str = (
        "https://rpc-testnet-0f871sgqn2.t.conduit.xyz"
    )
    CHAIN_ID: int = 261
    PRIVATE_KEY: str = (
        ""
    )
    CRYPTO_KEY: str = ""  # base64
    WALLET_GENERATION_TYPE: Literal["guru", "thirdweb_ecosystem"] = "guru"
    NATIVE_SEND_GAS_LIMIT: int = 21000


# Logging Configuration
class LoggingSettings(EnvBaseSettings):
    LOGGING_LEVEL: str = "INFO"


class EngineSettings(EnvBaseSettings):
    ENGINE_URL: str = "http://localhost:8080/engine-rest"
    ENGINE_USERNAME: str = "demo"
    ENGINE_PASSWORD: str = "demo"
    ENGINE_USERS_GROUP_ID: str = "camunda-admin"


class RabbitMQSettings(EnvBaseSettings):
    RABBIT_HOST: str = "rabbitmq"
    RABBIT_USER: str = "guest"
    RABBIT_PASSWORD: str = "<PASSWORD>"
    RABBIT_PORT: str = "5672"
    RABBIT_VHOST: str = "rabbit"
    RABBIT_EXCHANGE: str = "rabbit"
    RABBIT_EXCHANGE_TYPE: str = "direct"
    RABBIT_QUEUE: str = "app_listener"
    RABBIT_ROUTING_KEY: str = "enriched_dex_trade"


class ThirdWebAuthSettings(EnvBaseSettings):
    THIRDWEB_ENGINE_URL: str = ""
    THIRDWEB_ACCESS_KEY: str = ""
    THIRDWEB_BACKEND_WALLET: str = ""
    INTERNAL_NETWORKS: list[int] = [260, 261]\



class WorkerSettings(
    WorkerSettings,
    EngineSettings,
    APISettings,
    LoggingSettings,
    Web3Settings,
    RabbitMQSettings,
    ThirdWebAuthSettings
):
    DEBUG: bool = False

    class Config:
        env_file = ".env"


# Load environment variables from a .env file
load_dotenv()

worker_settings = WorkerSettings()
