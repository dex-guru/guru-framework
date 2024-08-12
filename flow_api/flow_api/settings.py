import os

from async_fastapi_jwt_auth import AuthJWT
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://db.sqlite3")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DATABASE = int(os.getenv("REDIS_DATABASE", 0))
SYS_KEY = os.getenv("SYS_KEY", "secret")
CACHE = os.getenv("CACHE", "redis")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
WAREHOUSE_URL = os.getenv("WAREHOUSE_URL", "https://warehouse.dex.guru")


def database_url() -> str:
    db_host: str = os.getenv("DB_HOST") or "localhost"
    db_port: int = int(os.getenv("DB_PORT") or 5432)
    db_user: str = os.getenv("DB_USER") or "postgres"
    db_pass: str | None = os.getenv("DB_PASS", "postgres")
    db_name: str = os.getenv("DB_NAME") or "postgres"

    if db_pass:
        return f"postgres://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return f"postgres://{db_user}@{db_host}:{db_port}/{db_name}"


class AuthSettings(BaseModel):
    authjwt_secret_key: str = os.getenv("AUTHJWT_SECRET_KEY", "secret")
    authjwt_algorithm: str = os.getenv("AUTHJWT_ALGORITHM", "HS256")


@AuthJWT.load_config
def get_config():
    return AuthSettings()
