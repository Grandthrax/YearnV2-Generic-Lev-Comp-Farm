from itertools import count
from brownie import Wei, reverts
from useful_methods import (
    stateOfStrat,
    stateOfVault,
    deposit,
    wait,
    withdraw,
    harvest,
    assertCollateralRatio,
)
import brownie


def test_sweep(web3, strategy, dai, cdai, gov, comp):
    with brownie.reverts("!want"):
        strategy.sweep(dai, {"from": gov})

    strategy.sweep(comp, {"from": gov})

    strategy.sweep(cdai, {"from": gov})

    cbat = "0x6c8c6b02e7b2be14d4fa6022dfd6d75921d90e4e"

    strategy.sweep(cbat, {"from": gov})


def test_apr_dai(
    web3, chain, comp, vault, enormousrunningstrategy, whale, gov, dai, strategist
):
    
    enormousrunningstrategy.setProfitFactor(1, {"from": gov})
    #assert enormousrunningstrategy.profitFactor() == 1
    vault.setManagementFee(0, {"from": gov}) # set management fee to 0 so that time works
    

    enormousrunningstrategy.setMinCompToSell(1, {"from": gov})
    #enormousrunningstrategy.setMinWant(0, {"from": gov})
    #assert enormousrunningstrategy.minCompToSell() == 1
    enormousrunningstrategy.harvest({"from": gov})
    chain.sleep(21600)

    print("mgm fee: ", vault.managementFee())
    print("perf fee: ", vault.performanceFee())

    startingBalance = vault.totalAssets()

    stateOfStrat(enormousrunningstrategy, dai, comp)
    stateOfVault(vault, enormousrunningstrategy)

    for i in range(6):

        waitBlock = 25
        print(f"\n----wait {waitBlock} blocks----")
        #wait(waitBlock, chain)
        chain.mine(waitBlock)
        ppsBefore = vault.pricePerShare()
        

        harvest(enormousrunningstrategy, gov, vault)
        #wait 6 hours. shouldnt mess up next round as compound uses blocks
        print("Locked: ", vault.lockedProfit())
        assert vault.lockedProfit() > 0 # some profit should be unlocked
        chain.sleep(21600)
        chain.mine(1)
        
        ppsAfter = vault.pricePerShare()

        #stateOfStrat(enormousrunningstrategy, dai, comp)
        # stateOfVault(vault, enormousrunningstrategy)

        profit = (vault.totalAssets() - startingBalance).to("ether")
        strState = vault.strategies(enormousrunningstrategy)
        totalReturns = strState.dict()['totalGain']
        totaleth = totalReturns.to("ether")
        print(f"Real Profit: {profit:.5f}")
        difff = profit - totaleth
        print(f"Diff: {difff}")
        print(f"PPS: {ppsAfter}")

        print(f"PPS Diff: {ppsAfter - ppsBefore}")
        assert ppsAfter - ppsBefore > 0 # pps should have risen

        blocks_per_year = 2_300_000
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        ppsProfit = (ppsAfter - ppsBefore) / 1e18 / waitBlock * blocks_per_year
        apr = (totalReturns / startingBalance) * (blocks_per_year / time)
        print(f"implied apr assets: {apr:.8%}")
        print(f"implied apr pps: {ppsProfit:.8%}")
    vault.withdraw(vault.balanceOf(whale), {"from": whale})


def test_getting_too_close_to_liq(
    web3, chain, cdai, comp, vault, largerunningstrategy, whale, gov, dai
):

    stateOfStrat(largerunningstrategy, dai, comp)
    stateOfVault(vault, largerunningstrategy)
    largerunningstrategy.setCollateralTarget(Wei("0.7498 ether"), {"from": gov})
    deposit(Wei("1000 ether"), whale, dai, vault)

    balanceBefore = vault.totalAssets()
    collat = 0
    assert largerunningstrategy.tendTrigger(1e18) == False

    largerunningstrategy.harvest({"from": gov})
    deposits, borrows = largerunningstrategy.getCurrentPosition()
    collat = borrows / deposits
    print(collat)

    stateOfStrat(largerunningstrategy, dai, comp)
    stateOfVault(vault, largerunningstrategy)
    assertCollateralRatio(largerunningstrategy)

    lastCol = collat

    while largerunningstrategy.tendTrigger(1e18) == False:
        cdai.mint(0, {"from": gov})
        waitBlock = 100
        wait(waitBlock, chain)
        deposits, borrows = largerunningstrategy.getCurrentPosition()
        collat = borrows / deposits
        assert collat > lastCol
        lastCol = collat
        print("Collat ratio: ", collat)
        print("Blocks to liq: ", largerunningstrategy.getblocksUntilLiquidation())

    largerunningstrategy.tend({"from": gov})

    largerunningstrategy.setCollateralTarget(Wei("0.73 ether"), {"from": gov})
    assert largerunningstrategy.tendTrigger(1e18) == False
    largerunningstrategy.tend({"from": gov})
    assertCollateralRatio(largerunningstrategy)
    stateOfStrat(largerunningstrategy, dai, comp)
    stateOfVault(vault, largerunningstrategy)


def test_harvest_trigger(
    web3, chain, comp, vault, largerunningstrategy, whale, gov, dai
):
    largerunningstrategy.setMinCompToSell(Wei("0.01 ether"), {"from": gov})

    assert largerunningstrategy.harvestTrigger(Wei("1 ether")) == False

    # sleep a day
    chain.sleep(86401)
    chain.mine(1)
    assert largerunningstrategy.harvestTrigger(Wei("1 ether")) == True

    largerunningstrategy.harvest({"from": gov})

    assert largerunningstrategy.harvestTrigger(Wei("0.0002 ether")) == False
    deposit(Wei("100 ether"), whale, dai, vault)
    assert largerunningstrategy.harvestTrigger(Wei("0.0002 ether")) == True
    assert largerunningstrategy.harvestTrigger(Wei("0.006 ether")) == False

    largerunningstrategy.harvest({"from": gov})

    times = 0
    while largerunningstrategy.harvestTrigger(Wei("0.0002 ether")) == False:
        wait(50, chain)
        print(largerunningstrategy.predictCompAccrued().to("ether"), " comp prediction")
        times = times + 1
        assert times < 10

    assert times > 3

    largerunningstrategy.harvest({"from": gov})
