# Chainflow Automation Platform

## Table of Contents
- [Introduction](#introduction)
- [Guru Framework](#guru-framework)
   - [Components](#components)
   - [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Development Process Example: Arbitrage Bot](#development-process-example-arbitrage-bot)
- [License](#license)
- [Contributing](#contributing)


# Introduction

Introducing our cutting-edge Web3 Automation platform, built on the robust Guru Network. This platform leverages
advanced data warehouse feeds to empower users with data-rich decision-making capabilities for a variety of automation
scenarios, including DeFi applications.
Key Features

**Data-Driven Decision Making:** Utilize our comprehensive data warehouse feeds that aggregate and process vast amounts
of information, ensuring your automation decisions are informed by the latest and most relevant data.
Seamless Integration with DeFi: Specifically tailored for DeFi scenarios, our platform allows users to automate complex
financial workflows, optimize investment strategies, and manage assets with precision and efficiency.
User-Centric Automation: Design personalized automation flows that cater to individual or business needs, enabling
better control over financial activities and operations.
Advanced AI Orchestration: At the heart of our platform is AI-driven orchestration, which integrates seamlessly both
on-chain and off-chain elements, ensuring smooth and intelligent operational flows.
Benefits

**Enhanced Operational Efficiency:** Automate routine and complex tasks, reducing the need for manual intervention and
allowing more time for strategic decision-making.
Improved Accuracy and Speed: With data-driven insights at your disposal, make faster and more accurate decisions that
align with market dynamics and your strategic goals.
Scalability: Whether scaling operations, managing more assets, or integrating new tools, our platform grows with your
needs, providing robust scalability and adaptability.
Security and Reliability: Built on the secure and reliable Guru Network, our platform ensures that your data and
automated processes are protected against threats and disruptions.
Use Cases

**Automated Trading**: Implement sophisticated trading strategies that react in real-time to market changes and optimize
returns.
Risk Management: Automate risk assessment and management protocols to maintain the health and security of your financial
portfolios.
Portfolio Rebalancing: Utilize AI-driven algorithms to adjust your asset allocations dynamically based on predefined
criteria and market conditions

# Guru Framework

The Guru Framework is an advanced toolkit designed to facilitate the orchestration of complex Web3, Web2, and off-chain
processes. It enables developers and startups to build applications that integrate seamlessly across various
technological environments. The framework encompasses a Blockchain Business Process Automation (BBPA) Engine, Smart
Contracts, a Landing and GUI page, and a unified Telegram bot composer, along with specialized External Workers for
non-custodial execution and compute.

## Components

### BBPA Engine

Located in the `engine` directory, the BBPA Engine is the cornerstone of the framework, managing the automation and
orchestration of blockchain business processes. It allows for efficient integration and management of workflows across
Web3 and Web2 infrastructures.

### Smart Contracts

The `contracts` directory houses all the smart contracts used within the Guru Framework. These contracts are crucial for
handling operations such as transactions, interactions, and protocol-specific functions, ensuring secure and efficient
decentralized application operations.

### Landing and GUI Page

Found under the `gui` directory, this component offers the user interface for the Guru Framework. It provides an
intuitive graphical interface for users to easily interact with the underlying systems, facilitating the management and
orchestration of complex processes.

### External Workers

External Workers are defined in the `external_workers` directory. These are individual agents that provide non-custodial
execution and compute services, enabling secure and decentralized processing without requiring custody of user data or
assets.

### Telegram Bot Unified Composer

This tool, integrated into the framework, allows developers to create Telegram bots that can control and manage
processes within the Guru Framework. It simplifies the development and integration of Telegram as an interactive layer
for applications, enhancing user engagement and process management.

## Project Structure

```
guru-framework/
│
├── contracts/ # Smart contracts for blockchain interactions
├── engine/ # Core BBPA engine for process automation
├── external_workers/ # Individual agents for non-custodial execution and compute
├── gui/ # User interface components
└── README.md # This file
```

# Getting Started

To begin using the Guru Framework, clone the repository and follow the setup instructions provided in each component's
directory.

```bash
git clone https://github.com/dex-guru/guru-framework.git
cd guru-framework
```

**Repository URL:** [GURU Framework](https://github.com/dex-guru/guru-framework)

### Prerequisites
Make sure you have Docker and Docker Compose installed on your machine.

**Subdirectories:**
- `engine`
- `gui`
- `external_workers`

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

Create Process in Camunda Modeler:

Design your process in Camunda Modeler.
Save the BPMN file to engine/resources directory.
![image](https://github.com/dex-guru/guru-framework/assets/20139308/6a2b14c8-3d90-403b-8aa0-e27ee7d30db6)


#### Create Non-Custodial External Worker in Python:

Create a Python script for the external worker.
Example code from external_workers/testnet_arbitrage/get_last_price.py:
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

Define your database models.
Example code for an arbitrage bot model:
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

