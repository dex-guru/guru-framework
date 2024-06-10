// SPDX-License-Identifier: MIT
// Compatible with OpenZeppelin Contracts ^5.0.0
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Pausable.sol";
import {FunctionsClient} from "@chainlink/contracts@1.1.0/src/v0.8/functions/v1_0_0/FunctionsClient.sol";
import {ConfirmedOwner} from "@chainlink/contracts@1.1.0/src/v0.8/shared/access/ConfirmedOwner.sol";
import {FunctionsRequest} from "@chainlink/contracts@1.1.0/src/v0.8/functions/v1_0_0/libraries/FunctionsRequest.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";


contract GuruSeason2PassNFT is ERC721, ERC721Pausable, ERC721Enumerable, FunctionsClient, ConfirmedOwner {
    using FunctionsRequest for FunctionsRequest.Request;

    uint256 private _nextTokenId;
    uint256 public constant MINTING_END_TIME = 1722470400;     // 08/01/2024 @ 00:00am (GMT)
    uint256 public constant NFT_PER_ADDRESS_LIMIT = 1;
    bytes32 private MERKLE_ROOT;
    address private executor;

    // ChainLink functions vars
    bytes32 public s_lastRequestId;
    string public baseURI;
    bytes public s_lastError;

    error UnexpectedRequestID(bytes32 requestId);
    event Response(bytes32 indexed requestId, bytes response, bytes err);

    constructor(address initialOwner, address router, address executorAddress)
            ERC721("Guru Season 2 Pass NFT", "GURUNFT2") FunctionsClient(router) ConfirmedOwner(initialOwner)
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
        return "https://flow.gurunetwork.ai/seasons/2/";
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


    function sendRequest(
        string memory source,
        bytes memory encryptedSecretsUrls,
        uint8 donHostedSecretsSlotID,
        uint64 donHostedSecretsVersion,
        string[] memory args,
        bytes[] memory bytesArgs,
        uint64 subscriptionId,
        uint32 gasLimit,
        bytes32 donID
    ) external onlyOwnerOrExecutor returns (bytes32 requestId) {
        FunctionsRequest.Request memory req;
        req.initializeRequestForInlineJavaScript(source);
        if (encryptedSecretsUrls.length > 0)
            req.addSecretsReference(encryptedSecretsUrls);
        else if (donHostedSecretsVersion > 0) {
            req.addDONHostedSecrets(
                donHostedSecretsSlotID,
                donHostedSecretsVersion
            );
        }
        if (args.length > 0) req.setArgs(args);
        if (bytesArgs.length > 0) req.setBytesArgs(bytesArgs);
        s_lastRequestId = _sendRequest(
            req.encodeCBOR(),
            subscriptionId,
            gasLimit,
            donID
        );
        return s_lastRequestId;
    }

    function sendRequestCBOR(
        bytes memory request,
        uint64 subscriptionId,
        uint32 gasLimit,
        bytes32 donID
    ) external onlyOwnerOrExecutor returns (bytes32 requestId) {
        s_lastRequestId = _sendRequest(
            request,
            subscriptionId,
            gasLimit,
            donID
        );
        return s_lastRequestId;
    }

    function fulfillRequest(
        bytes32 requestId,
        bytes memory response,
        bytes memory err
    ) internal override {
        if (s_lastRequestId != requestId) {
            revert UnexpectedRequestID(requestId);
        }
        if (err.length == 0) {
            MERKLE_ROOT = bytes32(response);
         }
        s_lastError = err;
        emit Response(requestId, response, s_lastError);
    }

}