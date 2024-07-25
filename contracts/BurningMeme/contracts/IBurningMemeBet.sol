// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

interface IBurningMemeBet {
    // Event declarations
    event Mint(address indexed account, uint256 amount, uint256 totalSupply);
    event Burn(address indexed account, uint256 amount, uint256 totalSupply);
    error InsufficientValue(uint256 minimumValue, uint256 value);
    error BurnAmountTooHigh(uint256 maximumAmount, uint256 amount);
    error EtherTransferFailed(address to, uint256 value);

    // View functions
    function burnBalanceOf(address account) external view returns (uint256);
    function burnTotalSupply() external view returns (uint256);
    function mintTotalSupply() external view returns (uint256);
    function mintBalanceOf(address account) external view returns (uint256);
    function mintCost(uint256 amount) external view returns (uint256);
    function burnCost(uint256 amount) external view returns (uint256);
    function getBettingEndTimestamp() external view returns (uint256);

    // State-changing functions
    function mint(uint256 amount) external payable;
    function burn(uint256 amount) external payable;
    function defineWinners() external;
}
