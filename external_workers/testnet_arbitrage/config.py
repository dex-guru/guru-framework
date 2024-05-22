import os

TOPIC_NAME = os.getenv("TOPIC_NAME", "CrossChainArbitrage")
WEB3_URL = os.getenv("WEB3_URL", "https://telcoin.rpc.dex.guru/archive/2017")
CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://localhost:8080/engine-rest")
CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')
PRIVATE_KEY = os.getenv(
    "PRIVATE_KEY", "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
)
ROUTER_ADDRESS = os.getenv(
    "ROUTER_ADDRESS", "0x5eb15FedcCA9Cb9c5424167e329fd56905fFe0e3"
)

CAMUNDA_CLIENT_CONFIG = {
    "auth_basic": {"username": CAMUNDA_USERNAME, "password": CAMUNDA_PASSWORD},
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30,
}
