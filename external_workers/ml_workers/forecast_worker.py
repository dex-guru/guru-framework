import os
import requests
import json
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://localhost:8080/engine-rest')
MINDSDB_USER = os.getenv("MINDSDB_USER", "mindsdb")
MINDSDB_PASS = os.getenv("MINDSDB_PASS", "mindsdb")
MINDSDB_API_URL = 'http://0.0.0.0:47334'
MINDSDB_PROJECT_NAME = 'mindsdb'
WAREHOUSE_URL = os.getenv('WAREHOUSE_URL', 'http://localhost:5001')
WAREHOUSE_API_KEY = os.getenv('WAREHOUSE_API_KEY', 'SUAK8G8g28PgoTcNF6maTpmr59Th9Ssi5zvfojtj')

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

def get_model_name(camunda_user_id, data_source, engine):
    return f"{camunda_user_id}_{data_source}_{engine}"

def get_view_name(camunda_user_id, data_source, engine):
    return f"{camunda_user_id}_{data_source}_{engine}_view"

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

def delete_resource(url):
    try:
        response = requests.delete(url, auth=(MINDSDB_USER, MINDSDB_PASS))
        response.raise_for_status()
        print(f"Resource at {url} deleted successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to delete resource at {url}: {e}")

def create_model(variables):
    camunda_user_id = variables.get('camunda_user_id')
    network = variables.get('network')
    data_source = variables.get('data_source')
    engine = variables.get('engine')
    token_address = variables.get('token_address')
    timestamp_start = variables.get('timestamp_start')
    window = variables.get('window')
    horizon = variables.get('horizon')

    model_name = get_model_name(camunda_user_id, data_source, engine)

    if model_exists(MINDSDB_PROJECT_NAME, model_name):
        delete_resource(f"{MINDSDB_API_URL}/api/projects/{MINDSDB_PROJECT_NAME}/models/{model_name}")

    query = f"""
        CREATE MODEL {MINDSDB_PROJECT_NAME}.{model_name}
        FROM clickhouse_{network} (
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

    payload = {"query": query}

    try:
        response = requests.post(
            f"{MINDSDB_API_URL}/api/projects/{MINDSDB_PROJECT_NAME}/models",
            json=payload,
            auth=(MINDSDB_USER, MINDSDB_PASS)
        )
        response.raise_for_status()
        print(f"Model {model_name} created successfully: {response.json()}")
        variables['is_creating'] = True
        return TaskResult.complete(variables)
    except requests.exceptions.RequestException as e:
        print(f"Failed to create model {model_name}: {e}")
        return TaskResult.failure(error_message=str(e), error_details=str(e), max_retries=0, retry_timeout=0)

def check_model_status(variables):
    model_name = get_model_name(variables['camunda_user_id'], variables['data_source'], variables['engine'])

    try:
        response = requests.get(
            f"{MINDSDB_API_URL}/api/projects/{MINDSDB_PROJECT_NAME}/models/{model_name}",
            auth=(MINDSDB_USER, MINDSDB_PASS)
        )
        response.raise_for_status()
        model_status = response.json().get('status', 'unknown')
        variables['status'] = model_status
        print(f"Model status for {MINDSDB_PROJECT_NAME}.{model_name}: {model_status}")
        return TaskResult.complete(variables)
    except requests.exceptions.RequestException as e:
        print(f"Failed to get model status for {MINDSDB_PROJECT_NAME}.{model_name}: {e}")
        return TaskResult.failure(error_message=str(e), error_details=str(e), retries=0)

def create_view(variables):
    camunda_user_id = variables.get('camunda_user_id')
    data_source = variables.get('data_source')
    engine = variables.get('engine')
    token_address = variables.get('token_address')
    timestamp_start = variables.get('timestamp_start')
    project_name = MINDSDB_PROJECT_NAME
    network = variables.get('network', 'ethereum')

    view_name = get_view_name(camunda_user_id, data_source, engine)

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

    if model_exists(project_name, view_name):
        delete_resource(f"{MINDSDB_API_URL}/api/projects/{project_name}/views/{view_name}")

    try:
        response = requests.post(
            f"{MINDSDB_API_URL}/api/projects/{project_name}/views",
            json=payload,
            auth=(MINDSDB_USER, MINDSDB_PASS)
        )
        response.raise_for_status()
        print(f"View {view_name} created successfully: {response.json()}")
        return TaskResult.complete()
    except requests.exceptions.RequestException as e:
        print(f"Failed to create view {view_name}: {e}")
        return TaskResult.failure(error_message=str(e), error_details=str(e), retries=0)

def create_wh_query(variables):
    print(f"Handling create warehouse query for task: {variables}")
    camunda_user_id = variables.get('camunda_user_id')
    data_source = variables.get('data_source')
    engine = variables.get('engine')
    token_address = variables.get('token_address')

    url = f'{WAREHOUSE_URL}/api/data_sources'
    data_sources = requests.get(
        url=url,
        headers={
            'Content-Type': 'application/json',
            'Authorization': WAREHOUSE_API_KEY
        }
    ).json()

    try:
        mindsdb_ds = [i for i in data_sources if i['type'] == 'mindsdb'][-1]
    except IndexError as e:
        print(f"Failed to get datasource mindsdb: {e}")
        return TaskResult.failure(error_message=str(e), error_details=str(e), retries=0)

    try:
        model_name = get_model_name(camunda_user_id, data_source, engine)
        view_name = get_view_name(camunda_user_id, data_source, engine)
        query = f"""SELECT
                    *
                    FROM
                       mindsdb.{view_name} AS d
                    JOIN
                       mindsdb.{model_name} AS m
                       ON d.time = m.time
                    WHERE
                       d.token_address = '{token_address}'"""

        data = {
            "name": model_name,
            "query": query,
            "data_source_id": mindsdb_ds['id']
        }

        url = f'{WAREHOUSE_URL}/api/queries'
        response = requests.post(
            url=url,
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json',
                'Authorization': WAREHOUSE_API_KEY
            }
        )
        response.raise_for_status()

        variables['curl'] = f"""curl -X POST 
        'https://api.dev.dex.guru/wh/{model_name}?api_key={WAREHOUSE_API_KEY}' 
        -H 'Content-Type: application/json'"""
        variables['curl'] = variables['curl'] + "--data '{\"parameters\": {}}'"
        return TaskResult.complete(variables)
    except requests.exceptions.RequestException as e:
        print(f"Failed to create warehouse query for {view_name}: {e}")
        return TaskResult.failure(error_message=str(e), error_details=str(e), retries=0)

def retrain_model(variables):
    return create_model(variables)  # Simply call create_model as retrain logic is the same

def drop_model(variables):
    camunda_user_id = variables.get('camunda_user_id')
    data_source = variables.get('data_source')
    engine = variables.get('engine')
    project_name = MINDSDB_PROJECT_NAME

    model_name = get_model_name(camunda_user_id, data_source, engine)
    view_name = get_view_name(camunda_user_id, data_source, engine)

    model_url = f"{MINDSDB_API_URL}/api/projects/{project_name}/models/{model_name}"
    view_url = f"{MINDSDB_API_URL}/api/projects/{project_name}/views/{view_name}"

    try:
        delete_resource(view_url)
        delete_resource(model_url)
        return TaskResult.complete(variables)
    except requests.exceptions.RequestException as e:
        print(f"Failed to drop model or view: {e}")
        return TaskResult.failure(error_message=str(e), error_details=str(e), retries=0)

def handle_task(task: ExternalTask) -> TaskResult:
    topic = task.get_topic_name()
    handlers = {
        "ml_create_model": create_model,
        "ml_check_model_status": check_model_status,
        "ml_create_view": create_view,
        "ml_create_wh_query": create_wh_query,
        "ml_retrain_model": retrain_model,
        "ml_drop_model": drop_model
    }

    handler = handlers.get(topic)
    if handler:
        return handler(task.get_variables())
    else:
        print(f"Unknown topic: {topic}")
        return TaskResult.failure('unknown topic', 'Unknown topic', 0, 0)

if __name__ == '__main__':
    worker = ExternalTaskWorker(worker_id="ml_workers",
                                base_url=CAMUNDA_URL,
                                config=default_config)
    worker.subscribe(topic_names=TOPICS, action=handle_task)
