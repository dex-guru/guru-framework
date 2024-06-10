import os

CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')

DEFAULT_CONFIG = {
    "auth_basic": {"username": CAMUNDA_USERNAME, "password": CAMUNDA_PASSWORD},
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30,
}
DELAY_TOPIC_NAME = os.getenv("DELAY_TOPIC_NAME", "check_delay")
CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://localhost:8080/engine-rest")
PRIVATE_KEY = os.getenv(
    "PRIVATE_KEY", "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
)
WEB3_URL = os.getenv("WEB3_URL", "http://new-rpc-gw-prod.dexguru.biz/archive/261")
