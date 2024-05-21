// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {strings} from "@chainlink/contracts/src/v0.8/vendor/Strings.sol";


interface ITurnstile {
    function register(address recipient)
    external
    returns (uint256 beneficiaryTokenID);

    function assign(uint256 beneficiaryTokenID)
    external
    returns (uint256 beneficiaryTokenID_);

    function withdraw(
        uint256 tokenId,
        address payable recipient,
        uint256 amount
    ) external returns (uint256 amount_);

    function balances(uint256 tokenId) external view returns (uint256 amount);

    function getTokenId(address _smartContract) external view returns (uint256);

    function isRegistered(address _smartContract) external view returns (bool);
}

interface IChainFlowFactoryShort {
    function turnstile() external view returns (ITurnstile);

    function getAllDefinitions() external view returns (string[] memory);

    function createDefinition(
        string memory definitionId
    ) external;

    function changeOwner(address _newOwner) external;

}

interface IProcessDefinitionShort {

    enum ProcessInstanceStatus {
        NotCreated,
        InProgress,
        Completed,
        Failed
    }

    function owner() external view returns (address);

    function processDefinitionId() external view returns (string memory);

    function factory() external view returns (address);

    function startedProcessInstances() external view returns (string[] memory);

    function processInstance(string memory _processInstanceId) external view returns (string memory, ProcessInstanceStatus);

    function transferOwnership(address _newOwner) external;

    function createProcessInstance(string memory _processInstanceId) external;

    function completeProcessInstance(string memory _processInstanceId) external;

    function failProcessInstance(string memory _processInstanceId, string calldata _reason) external;
}
