const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("BurningMemeBet", function () {
  let BurningMemeBet, burningMemeBet, owner, addr1, addr2, initialOwner;
  const NAME = "BurningMeme";
  const SYMBOL = "BMB";
  const TRADING_TTL = 7 * 24 * 60 * 60; // 7 days

  beforeEach(async function () {
    [owner, addr1, addr2, initialOwner] = await ethers.getSigners();
    BurningMemeBet = await ethers.getContractFactory("BurningMemeBet");
    burningMemeBet = await BurningMemeBet.deploy(initialOwner.address, NAME, SYMBOL, TRADING_TTL);
    await burningMemeBet.deployed();
  });

  it("Should deploy with the correct initial values", async function () {
    expect(await burningMemeBet.name()).to.equal(NAME);
    expect(await burningMemeBet.symbol()).to.equal(SYMBOL);
    expect(await burningMemeBet.totalSupply()).to.equal(0);
    expect(await burningMemeBet.mintTotalSupply()).to.equal(0);
    expect(await burningMemeBet.burnTotalSupply()).to.equal(0);
    expect(await burningMemeBet.getBettingEndTimestamp()).to.be.closeTo(
      (await ethers.provider.getBlock()).timestamp + TRADING_TTL,
      2
    );
  });

  it("Should allow the owner to pause and unpause", async function () {
    await burningMemeBet.connect(initialOwner).pause();
    expect(await burningMemeBet.paused()).to.be.true;

    await burningMemeBet.connect(initialOwner).unpause();
    expect(await burningMemeBet.paused()).to.be.false;
  });

  it("Should allow minting tokens before betting end timestamp", async function () {
    const mintAmount = 10;
    const mintCost = await burningMemeBet.mintCost(mintAmount);

    await burningMemeBet.connect(addr1).mint(mintAmount, { value: mintCost });
    expect(await burningMemeBet.mintBalanceOf(addr1.address)).to.equal(mintAmount);
    expect(await burningMemeBet.mintTotalSupply()).to.equal(mintAmount);
    expect(await burningMemeBet.totalSupply()).to.equal(mintAmount);
  });

  it("Should revert minting tokens after betting end timestamp", async function () {
    const mintAmount = 10;
    const mintCost = await burningMemeBet.mintCost(mintAmount);

    // Increase time to past betting end timestamp
    await ethers.provider.send("evm_increaseTime", [TRADING_TTL + 1]);
    await ethers.provider.send("evm_mine", []);

    await expect(burningMemeBet.connect(addr1).mint(mintAmount, { value: mintCost }))
      .to.be.revertedWith("Betting is closed");
  });

  it("Should allow burning tokens before betting end timestamp", async function () {
    const burnAmount = 5;
    const mintAmount = 10;
    const mintCost = await burningMemeBet.mintCost(mintAmount);

    await burningMemeBet.connect(addr1).mint(mintAmount, { value: mintCost });
    const burnCost = await burningMemeBet.burnCost(burnAmount);

    await burningMemeBet.connect(addr1).burn(burnAmount, { value: burnCost });
    expect(await burningMemeBet.burnBalanceOf(addr1.address)).to.equal(burnAmount);
    expect(await burningMemeBet.totalSupply()).to.equal(mintAmount + burnAmount);
  });

  it("Should revert burning tokens after betting end timestamp", async function () {
    const burnAmount = 5;
    const mintAmount = 10;
    const mintCost = await burningMemeBet.mintCost(mintAmount);

    await burningMemeBet.connect(addr1).mint(mintAmount, { value: mintCost });

    // Increase time to past betting end timestamp
    await ethers.provider.send("evm_increaseTime", [TRADING_TTL + 1]);
    await ethers.provider.send("evm_mine", []);

    const burnCost = await burningMemeBet.burnCost(burnAmount);
    await expect(burningMemeBet.connect(addr1).burn(burnAmount, { value: burnCost }))
      .to.be.revertedWith("Betting is closed");
  });

  it("Should define winners correctly", async function () {
    const mintAmount1 = 10;
    const mintCost1 = await burningMemeBet.mintCost(mintAmount1);
    await burningMemeBet.connect(addr1).mint(mintAmount1, { value: mintCost1 });

    const burnAmount1 = 20;
    const mintAmount2 = 15;
    const mintCost2 = await burningMemeBet.mintCost(mintAmount2);
    await burningMemeBet.connect(addr2).mint(mintAmount2, { value: mintCost2 });
    const burnCost1 = await burningMemeBet.burnCost(burnAmount1);
    await burningMemeBet.connect(addr2).burn(burnAmount1, { value: burnCost1 });

    // Increase time to past betting end timestamp
    await ethers.provider.send("evm_increaseTime", [TRADING_TTL + 1]);
    await ethers.provider.send("evm_mine", []);

    // Check total supply before defining winners
    expect(await burningMemeBet.mintTotalSupply()).to.equal(mintAmount1 + mintAmount2);
    expect(await burningMemeBet.burnTotalSupply()).to.equal(burnAmount1);
    expect(await burningMemeBet.totalSupply()).to.equal(mintAmount1 + mintAmount2 + burnAmount1);

    await burningMemeBet.connect(initialOwner).defineWinners();

    expect(await burningMemeBet.mintTotalSupply()).to.equal(mintAmount1 + mintAmount2 + burnAmount1);
    expect(await burningMemeBet.burnTotalSupply()).to.equal(0);
    expect(await burningMemeBet.totalSupply()).to.equal(mintAmount1 + mintAmount2 + burnAmount1);

  });

  it("Should revert if winners are defined before betting end timestamp", async function () {
    await expect(burningMemeBet.connect(initialOwner).defineWinners())
      .to.be.revertedWith("Betting still in progress");
  });

  it("Should revert if winners are defined more than once", async function () {
    const mintAmount = 10;
    const mintCost = await burningMemeBet.mintCost(mintAmount);
    await burningMemeBet.connect(addr1).mint(mintAmount, { value: mintCost });

    // Increase time to past betting end timestamp
    await ethers.provider.send("evm_increaseTime", [TRADING_TTL + 1]);
    await ethers.provider.send("evm_mine", []);

    await burningMemeBet.connect(initialOwner).defineWinners();
    await expect(burningMemeBet.connect(initialOwner).defineWinners())
      .to.be.revertedWith("Winners have been already defined");
  });

  it("Should allow the owner to withdraw funds", async function () {
    const mintAmount = 10000000;
    const mintCost = await burningMemeBet.mintCost(mintAmount);
    await burningMemeBet.connect(addr1).mint(mintAmount, { value: mintCost });

    const initialOwnerBalance = await ethers.provider.getBalance(initialOwner.address);
    await burningMemeBet.connect(initialOwner).withdraw();
    const finalOwnerBalance = await ethers.provider.getBalance(initialOwner.address);

    expect(finalOwnerBalance).to.be.gt(initialOwnerBalance);
  });
});
