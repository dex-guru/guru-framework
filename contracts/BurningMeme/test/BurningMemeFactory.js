const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("BurningMemeFactory", function () {
  let BurningMemeFactory, burningMemeFactory, BurningMemeBet, owner, addr1, addr2;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    BurningMemeFactory = await ethers.getContractFactory("BurningMemeFactory");
    burningMemeFactory = await BurningMemeFactory.deploy(owner.address);
    BurningMemeBet = await ethers.getContractFactory("BurningMemeBet");
    await burningMemeFactory.deployed();
  });

  it("Should deploy with the correct initial owner", async function () {
    expect(await burningMemeFactory.owner()).to.equal(owner.address);
  });

  it("Should create a new BurningMemeBet and emit an event", async function () {
    const tx = await burningMemeFactory.createBurningMeme(addr1.address, "MemeToken", "MTK");
    const receipt = await tx.wait();
    const event = receipt.events.find(event => event.event === "BurningMemeCreated");

    expect(event.args.newBurningMeme).to.not.be.undefined;
    expect(await burningMemeFactory.getDeployedTokensCount()).to.equal(1);
  });

  it("Should return the correct number of deployed tokens", async function () {
    await burningMemeFactory.createBurningMeme(addr1.address, "MemeToken1", "MTK1");
    await burningMemeFactory.createBurningMeme(addr2.address, "MemeToken2", "MTK2");

    expect(await burningMemeFactory.getDeployedTokensCount()).to.equal(2);
  });

  it("Should update the bettingTTL and emit an event", async function () {
    const oldBettingTTL = await burningMemeFactory.bettingTTL();
    const newBettingTTL = 14 * 24 * 60 * 60; // 14 days

    await expect(burningMemeFactory.updateBettingTTL(newBettingTTL))
      .to.emit(burningMemeFactory, "BettingTTLUpdated")
      .withArgs(oldBettingTTL, newBettingTTL);

    expect(await burningMemeFactory.bettingTTL()).to.equal(newBettingTTL);
  });

  it("Should revert if non-owner tries to create a BurningMemeBet", async function () {
    await expect(
      burningMemeFactory.connect(addr1).createBurningMeme(addr1.address, "MemeToken", "MTK")
    ).to.be.revertedWithCustomError(burningMemeFactory, "OwnableUnauthorizedAccount");
  });

  it("Should revert if non-owner tries to update bettingTTL", async function () {

    await expect(
      burningMemeFactory.connect(addr1).updateBettingTTL(14 * 24 * 60 * 60)
    ).to.be.revertedWithCustomError(burningMemeFactory, "OwnableUnauthorizedAccount");
  });
});
