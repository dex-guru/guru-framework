# Guru Framework External Workers

## Overview

This repository contains **External Workers** for the [Guru Framework](https://github.com/dex-guru/guru-framework), a next-generation development platform that combines AI automation, Web3 integrations, and business workflow orchestration. These workers are designed to execute blockchain-related tasks as part of automated business processes orchestrated by the **GURU Engine** (BPMN workflow engine).

---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Extending Workers](#extending-workers)
- [Integration with Guru Framework](#integration-with-guru-framework)
- [License](#license)

---

## Features
- **Non-custodial blockchain operations**: Securely manage wallets, sign and send transactions, and handle token approvals without direct custody of user funds.
- **Plug-and-play workers**: Easily add or modify workers for new business logic or blockchain operations.
- **GURU Engine integration**: Workers subscribe to GURU Engine topics and execute tasks as part of BPMN workflows.
- **Multi-chain support**: Easily configurable for different EVM-compatible blockchains.
- **Secure key management**: Private keys are encrypted and never exposed in plaintext.
- **Modular and scalable**: Each worker runs independently and can be scaled horizontally.

---

## Architecture

### How It Works
1. **GURU Engine** orchestrates business workflows and creates external tasks (e.g., token transfer, wallet creation).
2. **External Workers** (this repo) subscribe to specific topics and poll for new tasks from the engine.
3. **Worker scripts** execute blockchain operations (e.g., send transaction, approve token) and report results back to the GURU Engine.
4. **Configuration** is managed via environment variables and `.env` files, supporting multiple blockchains and deployment environments.

### Typical Workflow
- User triggers an action (e.g., via GUI or API).
- GURU Engine creates a task (e.g., `wallet_native_transfer`).
- The corresponding worker picks up the task, executes the blockchain logic, and returns the result (e.g., transaction hash).
- The workflow continues based on the result.

---

## Directory Structure

```
worker/
├── wallet/                # Blockchain wallet logic and worker scripts
│   ├── wallet_interfaces.py      # Wallet abstraction and implementations
│   ├── approve_token.py          # ERC20 token approval worker
│   ├── execute_transaction.py    # Transaction execution worker
│   ├── native_transfer.py        # Native token transfer worker
│   ├── treasury_transfer.py      # Treasury operations worker
│   └── generate.py               # Wallet generation logic
├── common/                # Shared utilities
│   └── utils.py
├── settings/              # Configuration and environment settings
│   └── worker.py
├── tests/                 # Unit tests
├── create_wallet.py       # Standalone wallet creation script
├── entrypoint.sh          # Entrypoint for Docker container
├── Dockerfile             # Docker build file
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)

### Clone the Repository
```bash
git clone https://github.com/dex-guru/guru-framework.git
cd guru-framework/worker
```

### Install Dependencies (for local development)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Configuration

All configuration is managed via environment variables and `.env` files. See `settings/worker.py` for all available options. Key settings include:
- **ENGINE_URL**: GURU Engine REST API endpoint
- **ENGINE_USERNAME / ENGINE_PASSWORD**: GURU Engine credentials
- **FLOW_API_URL / FLOW_API_SYS_KEY**: API for wallet/user management
- **RPC_URL / CHAIN_ID**: Blockchain node endpoint and chain ID
- **PRIVATE_KEY / CRYPTO_KEY**: Treasury wallet private key and encryption key
- **THIRDWEB_ENGINE_URL / THIRDWEB_ACCESS_KEY**: Thirdweb integration

You can provide environment variables via Docker Compose, `.env` files, or directly in your shell.

---

## Usage

### Running with Docker

The recommended way to run the workers is via Docker Compose as part of the full Guru Framework stack:

```yaml
services:
  external-workers:
    build:
      context: ./external_workers
    container_name: chainflow-external-workers
    environment:
      - WORKER_SCRIPTS=wallet/execute_transaction.py,wallet/native_transfer.py  # Add more as needed
      - CAMUNDA_URL=http://engine:8080/engine-rest
      - CAMUNDA_USER=demo
      - CAMUNDA_PASSWORD=demo
    networks:
      - chainflow-net
    volumes:
      - ./external_workers/envs:/app/envs
    depends_on:
      - engine
```

Or run a worker directly:

```bash
python wallet/execute_transaction.py
```

### Entrypoint Script
- `entrypoint.sh` allows running multiple workers in parallel, each with its own environment file (see `envs/`).
- Specify which workers to run using the `WORKER_SCRIPTS` environment variable (comma-separated list).

---

## Development

- Add new worker scripts in the `wallet/` directory for new GURU Engine topics.
- Use the `common/utils.py` utilities for worker setup and Web3 integration.
- Update `requirements.txt` for new dependencies.
- Use the provided configuration system in `settings/worker.py` for new settings.

---

## Testing

Unit tests are located in the `tests/` directory. To run tests:

```bash
pytest tests/
```

---

## Extending Workers

To add a new worker:
1. Create a new script in `wallet/` (or another appropriate directory).
2. Implement a handler function that processes the GURU Engine task.
3. Use `common/utils.py`'s `setup_worker` to subscribe to the topic.
4. Add the script to the `WORKER_SCRIPTS` environment variable in Docker Compose or your shell.

Example skeleton:
```python
from camunda.external_task.external_task_worker import ExternalTask
from common.utils import setup_worker

def handle_task(task: ExternalTask):
    # Your logic here
    return task.complete({"result": "ok"})

if __name__ == "__main__":
    setup_worker("your_topic", handle_task)
```

---

## Integration with Guru Framework

- These workers are designed to be used as the `external_workers` service in the Guru Framework's Docker Compose setup.
- They interact with the GURU Engine, Flow API, and blockchain networks as part of end-to-end business workflows.
- You can build your own DexGuru-grade apps by combining these workers with the rest of the Guru Framework stack.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details. 