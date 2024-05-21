import datetime
import os

import pandas as pd
import requests
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from ta.trend import SMAIndicator

TOPIC_NAME = os.getenv('TOPIC_NAME', "strategy_execution")
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://localhost:8080/engine-rest')
CAMUNDA_USERNAME = os.getenv('CAMUNDA_USERNAME', 'demo')
CAMUNDA_PASSWORD = os.getenv('CAMUNDA_PASSWORD', 'demo')
WAREHOUSE_API_KEY = os.getenv('WAREHOUSE_API_KEY', 'LcpfV5xdJ3Cw5o4SF3vWzXTC9HJFkrRCztg3Riov')
WAREHOUSE_REST_URL = os.getenv('WAREHOUSE_REST_URL', 'https://api.dev.dex.guru/wh/copy_of_202_candles_for_token_in_pool')

NETWORK = "canto"

# configuration for the Client
default_config = {
    "auth_basic": {"username": CAMUNDA_USERNAME, "password": CAMUNDA_PASSWORD},
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30
}


def check_sma_crossovers(data):
    # Convert data into a DataFrame
    df = pd.DataFrame(data)
    df['candle_datetime'] = pd.to_datetime(df['candle_datetime'])
    df.sort_values('candle_datetime', inplace=True)

    # Calculate SMA for 3 and 7 periods using ta library
    sma3 = SMAIndicator(df['close'], window=3)
    df['SMA3'] = sma3.sma_indicator()
    sma7 = SMAIndicator(df['close'], window=7)
    df['SMA7'] = sma7.sma_indicator()

    # Identify crossovers
    # SMA3 crosses above SMA7
    df['cross_above'] = (df['SMA3'] > df['SMA7']) & (df['SMA3'].shift(1) < df['SMA7'].shift(1))
    # SMA3 crosses below SMA7
    df['cross_below'] = (df['SMA3'] < df['SMA7']) & (df['SMA3'].shift(1) > df['SMA7'].shift(1))

    return df[['candle_datetime', 'SMA3', 'SMA7', 'cross_above', 'cross_below']]


def handle_task(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    token_address = variables.get('token_address')
    is_backtesting = variables.get('is_backtesting')

    if not is_backtesting:
        now = datetime.datetime.utcnow()
        datetime_end = now.strftime("%Y-%m-%d %H:%M")
        datetime_start = (now - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M")

    body = {"parameters": {
                "network": NETWORK,
                "token_address": token_address,
                "datetime_start": datetime_start,
                "datetime_end": datetime_end}}
    resp = requests.post(
        f"{WAREHOUSE_REST_URL}?api_key={WAREHOUSE_API_KEY}",
        json=body
    )

    candles = resp.json()

    indicators = check_sma_crossovers(candles)
    if not indicators.empty:
        last_signal = indicators.iloc[-1]

        if last_signal['cross_below']:
            return task.complete(global_variables=variables, local_variables={'trading_signal': 'buy'})

        if last_signal['cross_above']:
            return task.complete(global_variables=variables, local_variables={'trading_signal': 'sell'})

    return task.complete(global_variables=variables, local_variables={'trading_signal': ''})


if __name__ == '__main__':
    ExternalTaskWorker(worker_id="trading_strategy_worker",
                       base_url=CAMUNDA_URL,
                       config=default_config).subscribe([TOPIC_NAME], handle_task)