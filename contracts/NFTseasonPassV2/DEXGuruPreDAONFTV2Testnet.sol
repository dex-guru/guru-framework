// SPDX-License-Identifier: MIT
// Compatible with OpenZeppelin Contracts ^5.0.0
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";


contract GuruSeason2PassNFT is ERC721, ERC721Pausable, ERC721Enumerable, Ownable {
    uint256 private _nextTokenId;
    uint256 public constant MINTING_END_TIME = 1722470400;     // 08/01/2024 @ 00:00am (GMT)
    uint256 public constant NFT_PER_ADDRESS_LIMIT = 1;
    bytes32 private MERKLE_ROOT;
    address private executor;

    constructor(address initialOwner, address executorAddress)
            ERC721("Guru Season 2 Pass NFT", "GURUNFT2") Ownable(initialOwner)
        {
            executor = executorAddress;
        }

    modifier onlyOwnerOrExecutor() {
        require(msg.sender == owner() || msg.sender == executor, "Caller is not the owner or the executor of the contract");
        _;
    }

    function setExecutor(address executorAddress) external onlyOwner {
        executor = executorAddress;
    }

    function merkleRoot() public view onlyOwnerOrExecutor returns(bytes32) {
        return MERKLE_ROOT;
    }

    function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }

    function _baseURI() internal pure override returns (string memory) {
        return "https://flow.gurunetwork.ai/seasons/2/chain/261/token/";
    }

    function safeMint(bytes32[] calldata proof) public {
        require(balanceOf(msg.sender) < NFT_PER_ADDRESS_LIMIT, "You have reached max number of NFT!");
        require(block.timestamp <= MINTING_END_TIME, "SeasonPass has been sold out!");
        bytes32 leaf = keccak256(bytes.concat(keccak256(abi.encode(msg.sender))));
        require(MerkleProof.verify(proof, MERKLE_ROOT, leaf), "Invalid proof");
        uint256 tokenId = _nextTokenId++;
        _safeMint(msg.sender, tokenId);
    }

    // The following functions are overrides required by Solidity.

    function _update(address to, uint256 tokenId, address auth)
        internal
        override(ERC721, ERC721Enumerable, ERC721Pausable)
        returns (address)
    {
        return super._update(to, tokenId, auth);
    }

    function _increaseBalance(address account, uint128 value)
        internal
        override(ERC721, ERC721Enumerable)
    {
        super._increaseBalance(account, value);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721Enumerable)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    function updateMerkleRoot (bytes32 newMerkleRoot) public onlyOwnerOrExecutor {
        MERKLE_ROOT = newMerkleRoot;
    }

}