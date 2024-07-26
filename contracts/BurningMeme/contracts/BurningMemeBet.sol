// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import { IBurningMemeBet } from "./IBurningMemeBet.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { ERC20Pausable } from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";


// todo add fees to guru 2% of total supply.
// deploy on other chains common erc20 with fee.
//
//this contract only for guru network
contract BurningMemeBet is ERC20, ERC20Pausable, IBurningMemeBet, Ownable {
    mapping(address account => uint256) private _burnBalances;
    mapping(address account => uint256) private _mintBalances;
    uint256 private _burnTotalSupply = 0;
    uint256 private _mintTotalSupply = 0;

    bool private _isWinnersDefined = false;
    uint256 private immutable BETTING_END_TIMESTAMP;

    constructor(address initialOwner, string memory _name, string memory _symbol, uint256 _trading_ttl)
        ERC20(_name, _symbol)
        Ownable(initialOwner)
    {
        BETTING_END_TIMESTAMP = block.timestamp + _trading_ttl;
    }

    function mint(uint256 amount_) external payable override {
        require(block.timestamp < BETTING_END_TIMESTAMP, "Betting is closed");
        uint256 cost = mintCost(amount_);

        if (msg.value < cost) {
            revert InsufficientValue(cost, msg.value);
        }

        _mintVote(msg.sender, amount_);

        if (msg.value > cost) {
            (bool sent,) = msg.sender.call{value: msg.value - cost}("");
            if (!sent) {
                revert EtherTransferFailed(msg.sender, msg.value - cost);
            }
        }
        emit Mint(msg.sender, amount_, totalSupply());
    }

    function _mintVote(address account, uint256 amount_) private {
        _mintBalances[account] += amount_;
        _mintTotalSupply += amount_;
        emit Transfer(address(0), account, amount_);
    }

    function burn(uint256 amount_) external payable {
        require(block.timestamp < BETTING_END_TIMESTAMP, "Betting is closed");
        uint256 proceeds = burnCost(amount_);
        address sender = msg.sender;

        if (msg.value < proceeds) {
            revert InsufficientValue(proceeds, msg.value);
        }

        _burnVote(sender, amount_);

        if (msg.value > proceeds) {
            (bool sent,) = sender.call{value: msg.value - proceeds}("");
            if (!sent) {
                revert EtherTransferFailed(sender, msg.value - proceeds);
            }
        }

        emit Burn(sender, amount_, totalSupply());
    }

    function _burnVote(address account, uint256 amount) private {
        _burnBalances[account] += amount;
        _burnTotalSupply += amount;
        emit Transfer(address(0), account, amount);
    }

    function mintCost(uint256 amount_) public view override returns (uint256) {
        // The sum of the prices of all tokens already minted
        uint256 sumPricesCurrentTotalSupply = _sumOfPriceToNTokens(mintTotalSupply());
        // The sum of the prices of all the tokens already minted + the tokens to be newly minted
        uint256 sumPricesNewTotalSupply = _sumOfPriceToNTokens(mintTotalSupply() + amount_);

        return sumPricesNewTotalSupply - sumPricesCurrentTotalSupply;
    }

    function burnCost(uint256 amount_) public view override returns (uint256) {
        // The sum of the prices of all the tokens already minted
        uint256 sumBeforeBurn = _sumOfPriceToNTokens(burnTotalSupply());
        // The sum of the prices of all the tokens after burning amount_
        uint256 sumAfterBurn = _sumOfPriceToNTokens(burnTotalSupply() + amount_);

        return sumAfterBurn - sumBeforeBurn;
    }

   // The following function is override required by Solidity.
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Pausable)
    {
        super._update(from, to, value);
    }

    function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }

    function totalSupply() public view override  returns (uint256) {
        return _burnTotalSupply + _mintTotalSupply;
    }

    function getBettingEndTimestamp() public view returns (uint256) {
        return BETTING_END_TIMESTAMP;
    }

    function defineWinners() public onlyOwner {
        require(block.timestamp > BETTING_END_TIMESTAMP, "Betting still in progress");
        require(!_isWinnersDefined, "Winners have been already defined");
        if (mintTotalSupply() > burnTotalSupply()) {
            _mintTotalSupply = mintTotalSupply() + burnTotalSupply();
            _burnTotalSupply = 0;
        }
        else {
            _burnTotalSupply = mintTotalSupply() + burnTotalSupply();
            _mintTotalSupply = 0;
        }
        _isWinnersDefined = true;
    }

    function burnBalanceOf(address account) public view returns (uint256) {
        return _burnBalances[account];
    }

    function burnTotalSupply() public view returns (uint256) {
        return _burnTotalSupply;
    }

    function mintTotalSupply() public view returns (uint256) {
        return _mintTotalSupply;
    }

    function mintBalanceOf(address account) public view returns (uint256) {
        return _mintBalances[account];
    }


    function decimals() public pure override returns (uint8) {
        return 0;
    }

    // The price of *all* tokens from number 1 to n.
    function _sumOfPriceToNTokens(uint256 n_) internal pure returns (uint256) {
        return n_ * (n_ + 1) * (2 * n_ + 1) / 6;
    }

    function withdraw() public onlyOwner {
        uint256 amount = address(this).balance;
        (bool sent,) = msg.sender.call{value: amount}("");
        if (!sent) {
            revert EtherTransferFailed(msg.sender, amount);
        }
    }
}
