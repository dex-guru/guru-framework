// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import "./MemeCoin.sol";
import "./BurnCoin.sol";

contract MemeCoinFactory is Ownable {
    address[] private _memeCoinAddresses;
    address private _burnCoinAddress;
    
    constructor(address _initialOwner) Ownable(_initialOwner) {}

    event MemeCoinCreated(address indexed addr, string name, string symbol);
    event BurnCoinCreated(address indexed addr);

    function getMemeCoinAddresses() public view returns (address[] memory) {
        return _memeCoinAddresses;
    }

    function deployMemeCoin(
        uint256 _initialSupply,
        string memory name,
        string memory symbol
    ) external onlyOwner returns (address) {
        IERC20 newToken = new MemeCoin(name, symbol, _initialSupply);
        address newTokenAddress = address(newToken);
        _memeCoinAddresses.push(newTokenAddress);
        emit MemeCoinCreated(newTokenAddress, name, symbol);
        return newTokenAddress;
    }

    function deployBurnCoin(uint256 supply) external onlyOwner {
        require(_burnCoinAddress == address(0), "BurnCoin already deployed");
        bytes memory bytecode = type(BurnCoin).creationCode;
        bytecode = abi.encodePacked(bytecode, abi.encode(owner(), supply));

        // TODO: should we get salt from params?
        bytes32 salt = keccak256(abi.encodePacked(bytes1(0xff)));

        address token;
        assembly {
            token := create2(0, add(bytecode, 0x20), mload(bytecode), salt)
            if iszero(extcodesize(token)) {
                revert(0, 0)
            }
        }

        _burnCoinAddress = token;
        emit BurnCoinCreated(_burnCoinAddress);
    }
}