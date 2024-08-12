# Guru Framework

## Table of Contents
- [Introduction](#introduction)
- [Guru Framework](#guru-framework)
   - [Components](#components)
   - [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Development Process Example: Arbitrage Bot](#development-process-example-arbitrage-bot)
- [License](#license)
- [Contributing](#contributing)


## Introduction

Welcome to the Guru Framework, your ultimate toolkit for building sophisticated Web3 applications. Built on the robust Guru Network, our framework empowers developers with advanced tools for AI orchestration and Web3 automation. Whether you're working on DeFi applications, automated trading, or blockchain integration, the Guru Framework simplifies and enhances your development process.

**Key Features:**
- **Data-Driven Decision Making:** Leverage comprehensive data warehouse feeds for informed automation decisions.
- **Seamless Integration with DeFi:** Automate complex financial workflows and optimize investment strategies.
- **User-Centric Automation:** Create personalized automation flows for various financial activities and operations.
- **Advanced AI Orchestration:** Integrate on-chain and off-chain elements seamlessly with AI-driven orchestration.


## Components

### BBPA Engine
Located in the `engine` directory, this is the core of the framework, managing the automation and orchestration of blockchain business processes.

### Smart Contracts
Found in the `contracts` directory, these handle secure and efficient decentralized application operations.

### GUI
The `gui` directory contains the user interface components, offering an intuitive graphical interface for managing processes.

### Flow API
The Flow API in the `flow_api` directory provides endpoints for creating and managing workflows programmatically.

### Telegram Bot Unified Composer
Integrated into the framework, this tool allows the creation of Telegram bots to control and manage processes.

### External Workers
Defined in the `external_workers` directory, these provide non-custodial execution and compute services.

### Orchestration Workers Contracts
Located in the `orchestration_workers` directory, these contracts facilitate workflow orchestration.

## Project Structure


```
guru-framework/
│
├── contracts/ # Smart contracts for blockchain interactions
├── engine/ # Core BBPA engine for process automation
├── external_workers/ # Individual agents for non-custodial execution and compute
├── flow_api/ # API for managing and integrating workflows
├── bot/ # Telegram bot unified composer
├── gui/ # User interface components
└── README.md # This file
```

## Getting Started

To begin using the Guru Framework, follow these steps:

### Prerequisites
Ensure you have Docker and Docker Compose installed.

**Steps:**

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/dex-guru/guru-framework
    cd guru-framework
    ```

2. **Create the `docker-compose.yaml` file:**

    ```yaml
    version: '3.8'

    services:
      engine:
        build:
          context: ./engine
        container_name: chainflow-engine
        environment:
          INSCRIPTIONS_HISTORY_ENABLED: 'false'
          RABBITMQ_ENABLED: 'false'
        ports:
          - "8080:8080"
        networks:
          - chainflow-net

      gui:
        build:
          context: ./gui
        container_name: chainflow-gui
        ports:
          - "3000:3000"
        networks:
          - chainflow-net

      external-workers:
        build:
          context: ./external_workers
        container_name: chainflow-external-workers
        environment:
          - WORKER_SCRIPTS=messaging/telegram_message_worker.py,testnet_arbitrage/get_last_price.py  # Add more worker scripts as needed
          - CAMUNDA_URL=http://engine:8080/engine-rest
          - CAMUNDA_USER=demo
          - CAMUNDA_PASSWORD=demo
        networks:
          - chainflow-net
        volumes:
          - ./external_workers/envs:/app/envs  # Mount the directory containing environment files
        depends_on:
          - engine

    networks:
      chainflow-net:
        driver: bridge
    ```

3. **Run the Docker Compose setup:**

    ```bash
    docker-compose up -d --build
    ```

#### Check Services

- **Engine:** Running on [http://localhost:8080](http://localhost:8080) - default user/pass is demo:demo
- **GUI:** Running on [http://localhost:3000](http://localhost:3000)
- **Workers:** Check workers running with `docker-compose ps`
```bash
➜  guru-framework git:(main) ✗ docker-compose ps
           Name                         Command               State           Ports         
--------------------------------------------------------------------------------------------
chainflow-engine             java -jar chainflow-engine.jar   Up      0.0.0.0:8080->8080/tcp
chainflow-external-workers   /app/entrypoint.sh               Up                            
chainflow-gui                ./entrypoint.sh npm start        Up      0.0.0.0:3000->3000/tcp
```

# Development Process Example: Arbitrage Bot

### Step-by-Step Guide:

Create Process in [Camunda Modeler](https://camunda.com/download/modeler/):

Design your process in Camunda Modeler.
Save the BPMN file to engine/resources directory.
![image](https://github.com/dex-guru/guru-framework/assets/20139308/6a2b14c8-3d90-403b-8aa0-e27ee7d30db6)


#### Create Non-Custodial External Worker in Python:

**Create Non-Custodial External Worker in Python:**
1. Create a Python script for the external worker.
2. Example code from `external_workers/testnet_arbitrage/get_last_price.py`:

```python
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
import requests

def handle_task(task: ExternalTask) -> TaskResult:
    # Your task logic here
    response = requests.get('https://api.example.com/get-price')
    if response.status_code == 200:
        price = response.json().get('price')
        print(f"Retrieved price: {price}")
        return task.complete({"price": price})
    else:
        return task.failure(error_message="Failed to fetch price")

worker = ExternalTaskWorker(worker_id="worker-id", base_url="http://localhost:8080/engine-rest")
worker.subscribe("get-last-price", handle_task)
```

### Create Postgres Model Code:

1. Define your database models.
2. Example code for an arbitrage bot model:
```python
Copy code
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ArbitrageBot(Base):
    __tablename__ = 'arbitrage_bots'
    id = Column(Integer, primary key=True, autoincrement=True)
    name = Column(String)
    profit = Column(Float)

engine = create_engine('postgresql://user:password@localhost/dbname')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are highly encouraged! Please consult the CONTRIBUTING.md document for details on our code of conduct, and
the process for submitting pull requests to the project.

