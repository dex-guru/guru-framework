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

To begin using the Guru Framework, clone the repository and follow the setup instructions provided in each component's directory.

```bash
git clone https://github.com/your-guru-framework-repo.git
cd guru-framework
```
## Prerequisites
Make sure you have dependencies installed  run the framework.

## Running the Framework
Each component within the Guru Framework can be operated independently according to the setup instructions provided in their respective directories.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing
Contributions are highly encouraged! Please consult the CONTRIBUTING.md document for details on our code of conduct, and the process for submitting pull requests to the project.

