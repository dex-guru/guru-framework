from __future__ import annotations
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


DIR = Path(__file__).absolute().parent.parent.parent
BOT_DIR = Path(__file__).absolute().parent.parent
LOCALES_DIR = f"{BOT_DIR}/locales"
I18N_DOMAIN = "messages"

load_dotenv()


class EnvBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class WebhookSettings(EnvBaseSettings):
    USE_WEBHOOK: bool = False
    WEBHOOK_BASE_URL: str = "https://xxx.ngrok-free.app"
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_SECRET: str = "Pl7U9AJUFb2"
    WEBHOOK_HOST: str = "localhost"
    WEBHOOK_PORT: int = 8080

    @property
    def webhook_url(self) -> str:
        if settings.USE_WEBHOOK:
            return f"{self.WEBHOOK_BASE_URL}{self.WEBHOOK_PATH}"
        return f"http://localhost:{settings.WEBHOOK_PORT}{settings.WEBHOOK_PATH}"


class BotSettings(WebhookSettings):
    BOT_TOKEN: str
    SUPPORT_URL: str | None = None
    RATE_LIMIT: int | float = 0.5  # for throttling control
    HEALTH_CHECK_TIMEOUT: int = 120  # seconds
    SERVICE_URL: str | None = "https://EXAMPLE.COM"
    FLOW_API: str | None = "http://localhost:8000"
    FLOW_SYS_KEY: str | None = "secret"


class CacheSettings(EnvBaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASS: str | None = None
    REDIS_DATABASE: int = 0

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASS:
            return f"redis://{self.REDIS_PASS}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"


class EngineSettings(EnvBaseSettings):
    ENGINE_ADMIN_PREFIX: str = "http://localhost:8080"
    ENGINE_URL: str = "http://localhost:8080/engine-rest"
    ENGINE_USERNAME: str = "demo"
    ENGINE_PASSWORD: str = "demo"
    ENGINE_USERS_GROUP_ID: str = "camunda-admin"


class AWSSettings(EnvBaseSettings):
    AWS_ACCESS_KEY_ID: str = "KEY"
    AWS_SECRET_ACCESS_KEY: str = "SECRET"
    AWS_REGION_NAME: str = "us-east-2"
    AWS_S3_BUCKET: str = "BUCKET"


class Settings(BotSettings, CacheSettings, EngineSettings, AWSSettings):
    DEBUG: bool = False

    SENTRY_DSN: str | None = None

    # AMPLITUDE_API_KEY: str  # or for example it could be POSTHOG_API_KEY

    class Config:
        env_file = '.env'

settings = Settings()
