import datetime
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

# Camunda URL and configuration
CAMUNDA_URL = 'http://localhost:8080/engine-rest'
TOPIC_NAME = 'calculate_timeframe'

# Configuration settings
default_config = {
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 30
}


def handle_calculate_timeframe_task(task: ExternalTask) -> TaskResult:
    """Generate a timeframe array based on backtest start and end dates."""
    # Retrieve variables
    variables = task.get_variables()
    backtest_start_str = variables.get('backtest_start')
    backtest_end_str = variables.get('backtest_end')

    # Convert strings to datetime objects considering the timezone offset
    try:
        backtest_start = datetime.datetime.strptime(backtest_start_str, '%Y-%m-%dT%H:%M:%S.%f%z')
        backtest_end = datetime.datetime.strptime(backtest_end_str, '%Y-%m-%dT%H:%M:%S.%f%z')
    except ValueError as e:
        error_message = f"Invalid date format: {e}"
        return task.failure(error_message=error_message, error_details="Ensure backtest dates use ISO format with timezone info")

    # Convert both datetime objects to UTC
    backtest_start = backtest_start.astimezone(datetime.timezone.utc)
    backtest_end = backtest_end.astimezone(datetime.timezone.utc)

    # Validate dates
    if backtest_start > backtest_end:
        return task.failure(error_message="Start date is after end date", error_details="Ensure backtest_start is before backtest_end")

    # Create a list with a 5-minute step
    step_in_minutes = 5
    step_in_seconds = step_in_minutes * 60
    timeframe = []

    current = backtest_start
    while current <= backtest_end:
        timeframe.append(current.isoformat().replace('+00:00', 'Z'))  # Replace the UTC offset with 'Z'
        current += datetime.timedelta(seconds=step_in_seconds)

    # Pass the generated timeframe array
    variables['timeframe'] = list(timeframe)
    return task.complete(global_variables=variables,
                         # local_variables={'timeframe': timeframe}
                         )


if __name__ == '__main__':
    # Start the external worker with topic subscription
    ExternalTaskWorker(worker_id="calculate_timeframe_worker",
                       base_url=CAMUNDA_URL,
                       config=default_config).subscribe([TOPIC_NAME], handle_calculate_timeframe_task)
