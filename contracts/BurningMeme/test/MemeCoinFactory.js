const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MemeCoinFactory", function () {
  let MemeCoinFactory, memeCoinFactory, owner, addr1, addr2;
  const INITIAL_SUPPLY = 1000;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    MemeCoinFactory = await ethers.getContractFactory("MemeCoinFactory");
    memeCoinFactory = await MemeCoinFactory.deploy(owner.address);
    await memeCoinFactory.deployed();
  });

  it("Should deploy with the correct initial owner", async function () {
    expect(await memeCoinFactory.owner()).to.equal(owner.address);
  });

  it("Should allow the owner to deploy a new MemeCoin", async function () {
    const tx = await memeCoinFactory.deployMemeCoin(INITIAL_SUPPLY, "MemeCoin", "MEME");
    const receipt = await tx.wait();
    const event = receipt.events.find(event => event.event === "MemeCoinCreated");

    expect(event.args.addr).to.not.be.undefined;
    expect(event.args.name).to.equal("MemeCoin");
    expect(event.args.symbol).to.equal("MEME");

    const memeCoinAddresses = await memeCoinFactory.getMemeCoinAddresses();
    expect(memeCoinAddresses.length).to.equal(1);
    expect(memeCoinAddresses[0]).to.equal(event.args.addr);
  });

  it("Should not allow non-owners to deploy a new MemeCoin", async function () {
    await expect(
      memeCoinFactory.connect(addr1).deployMemeCoin(INITIAL_SUPPLY, "MemeCoin", "MEME")
    ).to.be.revertedWithCustomError(memeCoinFactory, "OwnableUnauthorizedAccount");
  });

  it("Should allow the owner to deploy a BurnCoin", async function () {
    const tx = await memeCoinFactory.deployBurnCoin(INITIAL_SUPPLY);
    const receipt = await tx.wait();
    const event = receipt.events.find(event => event.event === "BurnCoinCreated");
    const burnCoinAddress = event.args.addr;

    const burnCoin = await ethers.getContractAt("BurnCoin", burnCoinAddress);
    expect(await burnCoin.totalSupply()).to.equal(ethers.utils.parseUnits(INITIAL_SUPPLY.toString(), 18));
    expect(await burnCoin.owner()).to.equal(owner.address);
  });

  it("Should not allow deploying BurnCoin more than once", async function () {
    await memeCoinFactory.deployBurnCoin(INITIAL_SUPPLY);
    await expect(memeCoinFactory.deployBurnCoin(INITIAL_SUPPLY)).to.be.revertedWith("BurnCoin already deployed");
  });

  it("Should not allow non-owners to deploy a BurnCoin", async function () {
    await expect(
      memeCoinFactory.connect(addr1).deployBurnCoin(INITIAL_SUPPLY)
    ).to.be.revertedWithCustomError(memeCoinFactory, "OwnableUnauthorizedAccount");
  });
});
