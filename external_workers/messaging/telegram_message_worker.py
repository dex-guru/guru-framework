import os
from urllib.parse import urlparse

import requests
import logging
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Camunda and Telegram Bot API Configuration
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://localhost:8080/engine-rest')
CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your-telegram-bot-token')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'your-telegram-chat-id')
TOPIC_NAME = os.getenv("TOPIC_NAME", "send_tg_message")

# Default External Worker Configuration
default_config = {
    "auth_basic": {"username": CAMUNDA_USERNAME, "password": CAMUNDA_PASSWORD},
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30
}

def handle_send_tg_message_task(task: ExternalTask) -> TaskResult:
    """Handle tasks related to sending a message to Telegram."""
    variables = task.get_variables()
    task_definition_key = variables.get('task_definition_key')
    alert_tasks = variables.get('tasks', [])

    for alert in alert_tasks:
        name = alert.get('name')
        process_instance_id = alert.get('processInstanceId')
        assignee = alert.get('assignee')
        created = alert.get('createTime')
        # Generate the URL link to Camunda Cockpit
        camunda_cockpit_url = f"http://{urlparse(CAMUNDA_URL).netloc}/camunda/app/cockpit/default/#/process-instance/{process_instance_id}/runtime"

        message = (
            f"\U0001F4A9 \n"
            f"Task name: {name} \n"
            f"Definition key: {task_definition_key} \n"
            f"Assignee: {assignee} \n"
            f"Create Time: {created} \n"
            f"Process Instance URL \n"
            f"{camunda_cockpit_url} \n"
        )

        # Prepare the request body for the Telegram API
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        body = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
        }

        try:
            response = requests.post(telegram_url, json=body)
            response.raise_for_status()
            logger.debug(f"Message sent to Telegram successfully: {response.json()}")
        except requests.exceptions.HTTPError as err:
            logger.error(f"Error sending message to Telegram: {err}")
            return task.failure("Sending message to Telegram failed",
                                str(err),
                                max_retries=3,
                                retry_timeout=5000)

        logger.info("Message sent to Telegram successfully.")
        return task.complete()


if __name__ == '__main__':
    logger.info("Starting the external task worker...")
    worker = ExternalTaskWorker(
        worker_id="telegram_message_worker",
        base_url=CAMUNDA_URL,
        config=default_config
    )

    logger.info("Subscribing to topic...")
    worker.subscribe([TOPIC_NAME], handle_send_tg_message_task)
    logger.info("Worker subscribed to topic.")
