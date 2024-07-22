// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "./BurningMeme.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

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
    ) public onlyOwner returns (address) {
        IBurningMeme newBurningMeme = new BurningMeme(initialOwner, name, symbol, bettingTTL);
        deployedBurningMemes.push(address(newBurningMeme));
        emit BurningMemeCreated(address(newBurningMeme));
        return address(newBurningMeme);
    }

    function getDeployedBurningMemes() public view returns (address[] memory) {
        return deployedBurningMemes;
    }

    function updateBettingTTL(uint256 _newBettingTTL) public onlyOwner {
        uint256 oldBettingTTL = bettingTTL;
        bettingTTL = _newBettingTTL;
        emit BettingTTLUpdated(oldBettingTTL, bettingTTL);
    }

}