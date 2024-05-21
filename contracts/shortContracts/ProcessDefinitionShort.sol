// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./Interfaces.sol";


contract ProcessDefinitionShort is IProcessDefinitionShort{
    /// declare state variables
    address private _factory;
    address private _owner;
    string private _processDefinitionId;

    // all started process instances
    string[] private _startedProcessInstancesList;

    struct ProcessInstance {
        string processInstanceId;
        ProcessInstanceStatus status;
    }
    mapping(string => ProcessInstance) private _processInstances;

    constructor(
        address initialOwner,
        string memory __processDefinitionId
    )
    {
        _factory = msg.sender;
        ITurnstile turnstile = IChainFlowFactoryShort(_factory).turnstile();
        uint256 csrTokenID = turnstile.getTokenId(_factory);
        turnstile.assign(csrTokenID);
        _owner = initialOwner;
        _processDefinitionId = __processDefinitionId;
    }

    /// declare modifiers

    modifier onlyOwner() {
        if (msg.sender != _owner) {
            revert("Function can be called by owner only");
        }
        _;
    }

    modifier processInstanceCreated(string memory _processInstanceId) {
        if (_processInstances[_processInstanceId].status != ProcessInstanceStatus.InProgress) {
            revert("Process instance not created!");
        }
        _;
    }

    modifier processInstanceCompleted(string memory _processInstanceId) {
        if (_processInstances[_processInstanceId].status >= ProcessInstanceStatus.Completed) {
            revert("Process instance not completed!");
        }
        _;
    }

    /// declare view functions

    function owner() public view returns (address) {
        return _owner;
    }

    function processDefinitionId() public view returns (string memory) {
        return _processDefinitionId;
    }

    function factory() public view returns (address) {
        return _factory;
    }

    function startedProcessInstances() public view returns (string[] memory) {
        return _startedProcessInstancesList;
    }

    function processInstance(string memory _processInstanceId) public view returns (string memory, ProcessInstanceStatus) {
        return (_processInstances[_processInstanceId].processInstanceId, _processInstances[_processInstanceId].status);
    }

    /// declare events

    event ProcessInstanceCreated(string processInstanceId);
    event ProcessInstanceCompleted(string processInstanceId);
    event ProcessInstanceFailed(string processInstanceId, string reason);
    event TransferOwnership(address newOwner);

    /// declare owner's functions

    function transferOwnership(address _newOwner) external onlyOwner {
        _owner = _newOwner;
        emit TransferOwnership(_newOwner);
    }

    function createProcessInstance(string memory _processInstanceId) onlyOwner external {
        require(_processInstances[_processInstanceId].status == ProcessInstanceStatus.NotCreated, "Process instance already created!");
        _processInstances[_processInstanceId] = ProcessInstance(
            _processInstanceId,
            ProcessInstanceStatus.InProgress
        );
        _startedProcessInstancesList.push(_processInstanceId);
        emit ProcessInstanceCreated(_processInstanceId);
    }

    function completeProcessInstance(string memory _processInstanceId) external onlyOwner {
        require(_processInstances[_processInstanceId].status == ProcessInstanceStatus.InProgress, "Process instance not in progress!");

        _processInstances[_processInstanceId].status = ProcessInstanceStatus.Completed;
        emit ProcessInstanceCompleted(_processInstanceId);
    }

    function failProcessInstance(string memory _processInstanceId, string calldata _reason) external onlyOwner {
        require(_processInstances[_processInstanceId].status == ProcessInstanceStatus.InProgress, "Process instance not in progress!");
        _processInstances[_processInstanceId].status = ProcessInstanceStatus.Failed;
        emit ProcessInstanceFailed(_processInstanceId, _reason);
    }

}