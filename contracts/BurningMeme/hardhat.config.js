/** @type import('hardhat/config').HardhatUserConfig */
require("@nomiclabs/hardhat-ethers");
require("@nomicfoundation/hardhat-chai-matchers")
module.exports = {
  solidity: {
    version: "0.8.26",
    settings: {
        optimizer: {
            enabled: true,
            runs: 200,
        },
        evmVersion: "cancun",
    }
  },
};
