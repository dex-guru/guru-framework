import os

TOPIC_NAME = os.getenv("TOPIC_NAME", "checkInviteQuote")
CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://localhost:8080/engine-rest")
CAMUNDA_USERNAME = os.getenv("CAMUNDA_USERNAME", "demo")
CAMUNDA_PASSWORD = os.getenv("CAMUNDA_PASSWORD", "demo")
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
SYS_KEY = os.getenv("SYS_KEY", "secret")
INVITES_LIMIT = int(os.getenv("INVITES_LIMIT", 5))

CAMUNDA_CLIENT_CONFIG = {
    "auth_basic": {"username": CAMUNDA_USERNAME, "password": CAMUNDA_PASSWORD},
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30,
}
