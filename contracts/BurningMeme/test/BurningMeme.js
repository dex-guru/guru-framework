const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("BurningMeme", function () {
  let BurningMeme;
  let burningMeme;
  let owner;
  let addr1;
  let addr2;
  let addrs;
  const name = "Burning Meme Token";
  const symbol = "BMT";
  const tradingTTL = 86400; // 1 day

  beforeEach(async function () {
    BurningMeme = await ethers.getContractFactory("BurningMeme");
    [owner, addr1, addr2, ...addrs] = await ethers.getSigners();
    burningMeme = await BurningMeme.deploy(owner.address, name, symbol, tradingTTL);
    await burningMeme.deployed();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await burningMeme.owner()).to.equal(owner.address);
    });

    it("Should have the correct name and symbol", async function () {
      expect(await burningMeme.name()).to.equal(name);
      expect(await burningMeme.symbol()).to.equal(symbol);
    });

    it("Should set the correct betting end timestamp", async function () {
      const blockTimestamp = (await ethers.provider.getBlock()).timestamp;
      const bettingEndTimestamp = await burningMeme.getBettingEndTimestamp();
      expect(bettingEndTimestamp.toNumber()).to.be.closeTo(blockTimestamp + tradingTTL, 2);
    });
  });

  describe("Minting", function () {
    it("Should mint tokens correctly", async function () {
      const mintAmount = 10;
      const mintCost = await burningMeme.mintCost(mintAmount);

      await burningMeme.connect(addr1).mint(mintAmount, { value: mintCost });
      const mintBalance = await burningMeme.mintBalanceOf(addr1.address);
      expect(mintBalance.toNumber()).to.equal(mintAmount);
      expect((await ethers.provider.getBalance(burningMeme.address)).toNumber()).to.equal(mintCost.toNumber());
    });

    it("Should revert if insufficient value is sent", async function () {
      const mintAmount = 10;
      const mintCost = await burningMeme.mintCost(mintAmount);

      await expect(
        burningMeme.connect(addr1).mint(mintAmount, { value: mintCost.sub(1) })
      ).to.be.revertedWith("InsufficientValue");
    });

    it("Should refund excess ether sent during minting", async function () {
      const mintAmount = 10;
      const mintCost = await burningMeme.mintCost(mintAmount);
      const excessAmount = ethers.utils.parseEther("1");

      const initialBalance = await ethers.provider.getBalance(addr1.address);
      const tx = await burningMeme.connect(addr1).mint(mintAmount, { value: mintCost.add(excessAmount) });
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed.mul(tx.gasPrice);

      const finalBalance = await ethers.provider.getBalance(addr1.address);

      expect(finalBalance).to.be.closeTo(initialBalance.sub(mintCost).sub(gasUsed), 1000); // Allowing small margin for error
    });
  });

  describe("Burning", function () {
    it("Should burn tokens correctly", async function () {
      const mintAmount = 10;
      const mintCost = await burningMeme.mintCost(mintAmount);

      await burningMeme.connect(addr1).mint(mintAmount, { value: mintCost });
      const burnProceeds = await burningMeme.burnProceeds(mintAmount);

      await burningMeme.connect(addr1).burn(mintAmount, { value: burnProceeds });

      expect(await burningMeme.balanceOf(addr1.address)).to.equal(0);
      expect(await ethers.provider.getBalance(burningMeme.address)).to.equal(0);

      const initialBalance = await ethers.provider.getBalance(addr1.address);
      const tx = await burningMeme.connect(addr1).burn(mintAmount, { value: burnProceeds });
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed.mul(tx.gasPrice);

      const finalBalance = await ethers.provider.getBalance(addr1.address);
      expect(finalBalance).to.be.closeTo(initialBalance.add(burnProceeds).sub(gasUsed), 1000); // Allowing small margin for error
    });

    it("Should revert if trying to burn after betting end", async function () {
      const mintAmount = 10;
      const mintCost = await burningMeme.mintCost(mintAmount);

      await burningMeme.connect(addr1).mint(mintAmount, { value: mintCost });

      await ethers.provider.send("evm_increaseTime", [tradingTTL + 1]);
      await ethers.provider.send("evm_mine");

      await expect(
        burningMeme.connect(addr1).burn(mintAmount, { value: ethers.utils.parseEther("1") })
      ).to.be.revertedWith("Betting is closed");
    });
  });

  describe("Utilities", function () {
    it("Should return the correct burn balance", async function () {
      const mintAmount = 10;
      const mintCost = await burningMeme.mintCost(mintAmount);

      await burningMeme.connect(addr1).mint(mintAmount, { value: mintCost });

      expect(await burningMeme.burnBalanceOf(addr1.address)).to.equal(0);

      await burningMeme.connect(addr1).burn(mintAmount, { value: ethers.utils.parseEther("1") });

      expect(await burningMeme.burnBalanceOf(addr1.address)).to.equal(mintAmount);
    });

    it("Should return the correct mint balance", async function () {
      const mintAmount = 10;
      const mintCost = await burningMeme.mintCost(mintAmount);

      await burningMeme.connect(addr1).mint(mintAmount, { value: mintCost });

      expect(await burningMeme.mintBalanceOf(addr1.address)).to.equal(mintAmount);
    });

    it("Should return correct total supply", async function () {
      const mintAmount = 10;
      const burnAmount = 5;
      const mintCost = await burningMeme.mintCost(mintAmount);
      const burnProceeds = await burningMeme.burnProceeds(burnAmount);

      await burningMeme.connect(addr1).mint(mintAmount, { value: mintCost });
      await burningMeme.connect(addr1).burn(burnAmount, { value: burnProceeds });

      expect(await burningMeme.totalSupply()).to.equal(mintAmount - burnAmount);
    });
  });

  describe("Winners Definition", function () {
    it("Should define winners correctly", async function () {
      const mintAmount1 = 10;
      const mintAmount2 = 20;
      const burnAmount = 5;
      const mintCost1 = await burningMeme.mintCost(mintAmount1);
      const mintCost2 = await burningMeme.mintCost(mintAmount2);
      const burnProceeds = await burningMeme.burnProceeds(burnAmount);

      await burningMeme.connect(addr1).mint(mintAmount1, { value: mintCost1 });
      await burningMeme.connect(addr2).mint(mintAmount2, { value: mintCost2 });

      await ethers.provider.send("evm_increaseTime", [tradingTTL + 1]);
      await ethers.provider.send("evm_mine");

      await burningMeme.connect(owner).defineWinners();

      expect(await burningMeme.burnTotalSupply()).to.equal(burnAmount);
      expect(await burningMeme.mintTotalSupply()).to.equal(mintAmount1 + mintAmount2);
      expect(await burningMeme.totalSupply()).to.equal(burnAmount + mintAmount1 + mintAmount2);
    });

    it("Should revert if winners are already defined", async function () {
      const mintAmount1 = 10;
      const mintCost1 = await burningMeme.mintCost(mintAmount1);

      await burningMeme.connect(addr1).mint(mintAmount1, { value: mintCost1 });

      await ethers.provider.send("evm_increaseTime", [tradingTTL + 1]);
      await ethers.provider.send("evm_mine");

      await burningMeme.connect(owner).defineWinners();

      await expect(burningMeme.connect(owner).defineWinners()).to.be.revertedWith("Winners have been already defined");
    });
  });
});
