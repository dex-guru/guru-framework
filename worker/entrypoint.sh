#!/bin/bash

# Wait for the Camunda engine to be available
/app/wait-for-it.sh engine 8080

# Check if WORKER_SCRIPTS environment variable is set
if [ -z "$WORKER_SCRIPTS" ]; then
  echo "No worker scripts specified. Exiting."
  exit 1
fi

# Convert the comma-separated list of worker scripts into an array
IFS=',' read -r -a workers <<< "$WORKER_SCRIPTS"

# Loop through the array and run each worker script in the background
for worker in "${workers[@]}"; do
  # Get the base name of the worker script without the extension and the directory path
  worker_base=$(basename "$worker" .py)
  worker_dir=$(dirname "$worker")

  # Source the environment variables for the worker script from the corresponding env directory
  if [ -f "./envs/${worker_dir}/${worker_base}.env" ]; then
    export $(grep -v '^#' "./envs/${worker_dir}/${worker_base}.env" | xargs)
  else
    echo "No environment file found for worker: ${worker_dir}/${worker_base}"
    exit 1
  fi

  echo "Starting worker: $worker with environment variables from envs/${worker_dir}/${worker_base}.env"
  python "$worker" &
done

# Wait for all background processes to finish
wait
