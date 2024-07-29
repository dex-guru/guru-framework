import os

from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
import requests
import json

MINDSDB_USER = os.getenv("MINDSDB_USER", "mindsdb")
MINDSDB_PASS = os.getenv("MINDSDB_PASS", "mindsdb")
MINDSDB_API_URL = 'http://0.0.0.0:47334'
MINDSDB_PROJECT_NAME = 'mindsdb'

default_config = {
    "auth_basic": {"username": "demo", "password": "demo"},
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30
}

# Define the topics to be subscribed to
TOPICS = [
    "ml_create_model",
    "ml_check_model_status",
    "ml_create_view",
    "ml_create_wh_query",
    "ml_retrain_model",
    "ml_drop_model"
]


def model_exists(project_name, model_name):
    try:
        response = requests.get(
            f"{MINDSDB_API_URL}/api/projects/{project_name}/models/{model_name}",
            auth=(MINDSDB_USER, MINDSDB_PASS)
        )
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return False
        print(f"HTTP error occurred: {http_err}")
        return False
    except Exception as err:
        print(f"Other error occurred: {err}")
        return False


def delete_model(project_name, model_name):
    try:
        response = requests.delete(
            f"{MINDSDB_API_URL}/api/projects/{project_name}/models/{model_name}",
            auth=(MINDSDB_USER, MINDSDB_PASS)
        )
        response.raise_for_status()
        print(f"Model {project_name}.{model_name} deleted successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to delete model {project_name}.{model_name}: {e}")


def handle_create_model(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    camunda_user_id = variables.get('camunda_user_id')
    data_source = variables.get('data_source')
    engine = variables.get('engine')
    token_address = variables.get('token_address')
    timestamp_start = variables.get('timestamp_start')
    window = variables.get('window')
    horizon = variables.get('horizon')

    model_name = f"{camunda_user_id}_{data_source}_{engine}"

    if model_exists(MINDSDB_PROJECT_NAME, model_name):
        delete_model(MINDSDB_PROJECT_NAME, model_name)

    # Construct the SQL query for model creation
    query = f"""
        CREATE MODEL {MINDSDB_PROJECT_NAME}.{model_name}
        FROM clickhouse_ethereum (
           SELECT 
              toUnixTimestamp(toStartOfHour(FROM_UNIXTIME(timestamp), 'UTC'), 'UTC') as time,
              token_address as token_address,  
              max(c_s).2 as price
           FROM {data_source}
           WHERE token_address = '{token_address}' AND timestamp >= {timestamp_start}
           GROUP BY time, token_address
        )
        PREDICT price
        ORDER BY time
        GROUP BY token_address
        HORIZON {horizon}
        WINDOW {window}
        USING ENGINE = '{engine}';
    """

    payload = {
        "query": query
    }

    try:
        # Make the HTTP request to create the model
        response = requests.post(
            f"{MINDSDB_API_URL}/api/projects/{MINDSDB_PROJECT_NAME}/models",
            json=payload,
            auth=(MINDSDB_USER, MINDSDB_PASS)
        )
        response.raise_for_status()
        print(f"Model {model_name} created successfully: {response.json()}")
        variables['is_creating'] = True
        return task.complete(variables)
    except requests.exceptions.RequestException as e:
        print(f"Failed to create model {model_name}: {e}")
        return task.failure(error_message=str(e), error_details=str(e), max_retries=0, retry_timeout=0)


def handle_check_model_status(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    camunda_user_id = variables.get('camunda_user_id')
    data_source = variables.get('data_source')
    engine = variables.get('engine')
    token_address = variables.get('token_address')
    timestamp_start = variables.get('timestamp_start')
    window = variables.get('window')
    horizon = variables.get('horizon')

    model_name = f"{camunda_user_id}_{data_source}_{engine}"

    try:
        response = requests.get(
            f"{MINDSDB_API_URL}/api/projects/{MINDSDB_PROJECT_NAME}/models/{model_name}",
            auth=(MINDSDB_USER, MINDSDB_PASS)
        )
        response.raise_for_status()
        model_status = response.json().get('status', 'unknown')
        variables['status'] = model_status
        print(f"Model status for {MINDSDB_PROJECT_NAME}.{model_name}: {model_status}")
        return task.complete(variables)
    except requests.exceptions.RequestException as e:
        print(f"Failed to get model status for {MINDSDB_PROJECT_NAME}.{model_name}: {e}")
        return task.failure(error_message=str(e), error_details=str(e), retries=0)


def handle_create_view(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    camunda_user_id = variables.get('camunda_user_id')
    data_source = variables.get('data_source')
    engine = variables.get('engine')
    token_address = variables.get('token_address')
    timestamp_start = variables.get('timestamp_start')
    project_name = MINDSDB_PROJECT_NAME
    network = variables.get('network', 'ethereum')

    view_name = f"{camunda_user_id}_{data_source}_{engine}_view"

    query = f"""
        SELECT 
            *
        FROM clickhouse_{network} (
            SELECT 
                toStartOfHour(FROM_UNIXTIME(timestamp), 'UTC') as time,
                token_address as token_address,  
                max(c_s).2 as price
            FROM {data_source}
            WHERE token_address = '{token_address}' AND timestamp >= {timestamp_start}
            GROUP BY time, token_address
        );
    """

    payload = {
        "view": {
            "name": view_name,
            "query": query
        }
    }

    try:
        print(f"Creating view with name: {view_name}")
        print(f"Query: {query}")
        # Make the HTTP request to create the view
        response = requests.post(
            f"{MINDSDB_API_URL}/api/projects/{project_name}/views",
            json=payload,
            auth=(MINDSDB_USER, MINDSDB_PASS)
        )
        response.raise_for_status()
        print(f"View {view_name} created successfully: {response.json()}")
        return task.complete()
    except requests.exceptions.RequestException as e:
        print(f"Failed to create view {view_name}: {e}")
        return task.failure(error_message=str(e), error_details=str(e), retries=0)



def handle_create_wh_query(task: ExternalTask) -> TaskResult:
    print(f"Handling create warehouse query for task: {task.get_variables()}")
    # Not implemented
    # return task.complete()


def handle_retrain_model(task: ExternalTask) -> TaskResult:
    print(f"Handling retrain model for task: {task.get_variables()}")
    # Not implemented
    # return task.complete()


def handle_drop_model(task: ExternalTask) -> TaskResult:
    print(f"Handling drop model for task: {task.get_variables()}")
    # Not implemented
    # return task.complete()


def handle_task(task: ExternalTask) -> TaskResult:
    topic = task.get_topic_name()

    if topic == "ml_create_model":
        return handle_create_model(task)
    elif topic == "ml_check_model_status":
        return handle_check_model_status(task)
    elif topic == "ml_create_view":
        return handle_create_view(task)
    elif topic == "ml_create_wh_query":
        return handle_create_wh_query(task)
    elif topic == "ml_retrain_model":
        return handle_retrain_model(task)
    elif topic == "ml_drop_model":
        return handle_drop_model(task)
    else:
        print(f"Unknown topic: {topic}")
        return task.failure('unknown topic', 'Unknown topic', 0, 0)


if __name__ == '__main__':
    worker = ExternalTaskWorker(worker_id="ml_workers",
                                base_url="http://localhost:8080/engine-rest",
                                config=default_config)
    worker.subscribe(topic_names=TOPICS, action=handle_task)

