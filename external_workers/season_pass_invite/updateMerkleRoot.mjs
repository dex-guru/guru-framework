import {Client, logger} from "camunda-external-task-client-js";

import ethers from "ethers";

import abiNonFunctionNFT from "./abiNonFunctionNFT.mjs";
import 'dotenv/config';
import {StandardMerkleTree} from "@openzeppelin/merkle-tree";


const contractAddress = process.env.CONTRACT_ADDRESS;

const engineConfig = {
    baseUrl: process.env.ENGINE_URL,
    use: logger,
    workerId: "update_merkle_tree",
    maxTasks: 1,
    lockDuration: 5000000,
    retries: 0,
    autoPoll: true,
};
const client = new Client(engineConfig);


const makeRequest = async (wallets) => {
    const explorerUrl = process.env.EXPLORER_URL;
    const privateKey = process.env.PRIVATE_KEY; // fetch PRIVATE_KEY
    const rpcUrl = process.env.RPC_URL;

    // Initialize functions settings
    const merkleRoot = generateMerkleRoot(wallets);

    // Initialize ethers signer and provider to interact with the contracts onchain
    if (!privateKey)
        throw new Error(
            "private key not provided - check your environment variables"
        );


    if (!rpcUrl)
        throw new Error(`rpcUrl not provided  - check your environment variables`);

    const provider = new ethers.providers.JsonRpcProvider(rpcUrl);

    const wallet = new ethers.Wallet(privateKey);
    const signer = wallet.connect(provider); // create ethers signer for signing transactions

    //////// CHECK IF NEED UPDATE //////////
    const contractNFT = new ethers.Contract(
        contractAddress,
        abiNonFunctionNFT,
        signer
    );
    const currentMerkleRoot = await contractNFT.merkleRoot();
    if (currentMerkleRoot === merkleRoot) {
        console.log(`\n✅ Merkle tree is up to date`);
        return
    }

    // Actual transaction call
    const transaction = await contractNFT.updateMerkleRoot(
        merkleRoot,
    );

    // Log transaction details
    console.log(
        `\n✅ Functions request sent! Transaction hash ${transaction.hash}. Waiting for a response...`
    );

    // wait for the transaction to be mined

    const receipt = await transaction.wait();

    if (receipt.status === 0) {
        console.log(`\n❌ Transaction failed: ${transaction.hash}`);
        throw new Error(`Transaction failed: ${transaction.hash}`);
    }

    console.log(
        `See your request in the explorer ${explorerUrl}/tx/${transaction.hash}`
    );
    return transaction.hash
};


async function markWalletsAsInvited() {
    const url = process.env.API_URL
    const sys_key = process.env.SYS_KEY
    const queryParams = new URLSearchParams({
        "only_updated": "false"
    })
    const response = await fetch(url + "?" + queryParams.toString(), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-SYS-KEY': sys_key
        },
    })
    if (response.status !== 200) {
        console.log("Failed to mark wallets as invited. Status", response.status)
        throw new Error(`Failed to mark wallets as invited. Status ${response.status}`)
    }
}

async function getExistingAddresses() {
    const url = process.env.API_URL
    const sys_key = process.env.SYS_KEY
    const queryParams = new URLSearchParams({
        "only_updated": "false"
    })
    const response = await fetch(url + "?" + queryParams.toString(), {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-SYS-KEY': sys_key
        },
    })
    if (response.status !== 200) {
        console.log("Failed to mark wallets as invited. Status", response.status)
        throw new Error(`Failed to mark wallets as invited. Status ${response.status}`)
    }
    return await response.json()
}


async function handleTask({task, taskService}) {
    try {
        const wallets = await getExistingAddresses();
        if (!wallets || wallets.length === 0) {
            console.log("No wallets to invite");
            return await taskService.complete(task);
        }

        const tx_hash = await makeRequest(wallets);
        await markWalletsAsInvited();
        return await taskService.complete(task);
    } catch (error) {
        console.log("Error processing task", error);
        logger.error(error);
        return await taskService.handleBpmnError(task, "CHAINLINK_CCIP_ERROR", error.message);
    }
}

function generateMerkleRoot(walletAddresses) {
    const walletsSet = new Set(walletAddresses.map(x => (x.toLowerCase())))
    const walletArrayOfArray = [...walletsSet].map(x => ([x]))
    return StandardMerkleTree.of(walletArrayOfArray, ['address']).root;
}

client.subscribe(
    "updateMerkleTree",
    handleTask
);
// const wallets = await getExistingAddresses();
// console.log(wallets);
// const merkleRoot = generateMerkleRoot(wallets);
// console.log(merkleRoot);
//
// const tx_hash = await makeRequest(wallets);
// await markWalletsAsInvited()
