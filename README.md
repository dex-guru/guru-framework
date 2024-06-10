# Chainflow Automation Platform

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

## Getting Started

To begin using the Guru Framework, clone the repository and follow the setup instructions provided in each component's
directory.

```bash
git clone https://github.com/dex-guru/guru-framework.git
cd guru-framework
```

## Prerequisites

Make sure you have dependencies installed run the framework.

## Running the Framework

Each component within the Guru Framework can be operated independently according to the setup instructions provided in
their respective directories.

#### Overview

This guide provides quick start instructions for the GURU project, including setting up the application with Camunda, FastAPI, and a GUI. It also describes the development process using an arbitrage bot example.

---

#### Quick Start

**Repository URL:** [GURU Framework](https://github.com/dex-guru/guru-framework)

##### 1. Setting Up the Application

**Subdirectories:**
- `camunda`
- `fastapi`
- `gui`

**Steps:**

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/dex-guru/guru-framework
   cd dep-guru-framework
   ```
Engine:

Ensure you have Docker installed.
Start Camunda:
```bash
docker-compose up -d
```
Deploy using Helm:
```bash
export KUBECONFIG=~/Downloads/stage-k8s.yaml 
helm upgrade --install chainflow-engine ./helm/engine --wait -n stage --set imageTag=1 --set appName=chainflow-engine --set kubeNamespace=stage
```
Available at:
Application: http://localhost:8080/camunda/app/welcome/default/
API: http://localhost:8080/engine-rest

Navigate to the FastAPI directory and install dependencies:
```bash
cd fastapi
pip install -r requirements.txt
Start the FastAPI server:
bash
Copy code
uvicorn main:app --reload
```
GUI:
Navigate to the GUI directory and install dependencies:
```bash
cd gui
npm install
Start the GUI application:
bash
Copy code
npm start
```
External Workers:

Build and start the external workers using Docker:
```bash
cd external_worker
docker build -t external-worker .
docker run external-worker
Development Process Example: Arbitrage Bot
```


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

