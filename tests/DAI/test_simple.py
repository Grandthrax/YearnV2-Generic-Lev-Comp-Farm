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
    web3, chain, comp, vault, enormousrunningstrategy, user, gov, dai
):
    whale = user
    stateOfStrat(enormousrunningstrategy, dai, comp)
    stateOfVault(vault, enormousrunningstrategy)
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
    stateOfStrat(enormousrunningstrategy, dai, comp)
    stateOfVault(vault, enormousrunningstrategy)

