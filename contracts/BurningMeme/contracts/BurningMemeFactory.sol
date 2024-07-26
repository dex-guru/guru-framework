// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./BurningMemeBet.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";

contract BurningMemeFactory is Ownable {

    uint256 public bettingTTL = 7 days;

    constructor (address initialOwner) Ownable(initialOwner) {}

    address[] public deployedBurningMemes;

    event BurningMemeCreated(address indexed newBurningMeme);
    event BettingTTLUpdated(uint256 indexed oldBettingTTL, uint256 indexed newBettingTTL);

    function createBurningMeme(
        address initialOwner,
        string memory name,
        string memory symbol
    ) external onlyOwner returns (address) {
        IBurningMemeBet newBurningMeme = new BurningMemeBet(initialOwner, name, symbol, bettingTTL);
        deployedBurningMemes.push(address(newBurningMeme));
        emit BurningMemeCreated(address(newBurningMeme));
        return address(newBurningMeme);
    }

    function getDeployedBurningMemes() public view returns (address[] memory) {
        return deployedBurningMemes;
    }

    function getDeployedTokensCount() public view returns (uint256) {
        return deployedBurningMemes.length;
    }

    function updateBettingTTL(uint256 _newBettingTTL) external onlyOwner {
        uint256 oldBettingTTL = bettingTTL;
        bettingTTL = _newBettingTTL;
        emit BettingTTLUpdated(oldBettingTTL, bettingTTL);
    }
}