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


def test_all(
    web3, chain, comp, live_dai_vault, live_strategy, user, dai, accounts
):
    whale = user
    vault = live_dai_vault
    strategy = live_strategy
    gov = accounts.at(vault.governance(), force=True)
    strategy.harvest({"from": gov})
    stateOfStrat(strategy, dai, comp)
    stateOfVault(vault, strategy)
    strategy.setProfitFactor(1, {"from": gov})
    #assert enormousrunningstrategy.profitFactor() == 1
    vault.setManagementFee(0, {"from": gov}) # set management fee to 0 so that time works


    strategy.setMinCompToSell(1, {"from": gov})
    #enormousrunningstrategy.setMinWant(0, {"from": gov})
    #assert enormousrunningstrategy.minCompToSell() == 1
    strategy.harvest({"from": gov})
    chain.sleep(21600)

    print("mgm fee: ", vault.managementFee())
    print("perf fee: ", vault.performanceFee())

    startingBalance = vault.totalAssets()

    stateOfStrat(strategy, dai, comp)
    stateOfVault(vault, strategy)

    for i in range(6):

        waitBlock = 25
        print(f"\n----wait {waitBlock} blocks----")
        #wait(waitBlock, chain)
        chain.mine(waitBlock)
        ppsBefore = vault.pricePerShare()


        harvest(strategy, gov, vault)
        #wait 6 hours. shouldnt mess up next round as compound uses blocks
        print("Locked: ", vault.lockedProfit())
        assert vault.lockedProfit() > 0 # some profit should be unlocked
        chain.sleep(21600)
        chain.mine(1)

        ppsAfter = vault.pricePerShare()

        #stateOfStrat(enormousrunningstrategy, dai, comp)
        # stateOfVault(vault, enormousrunningstrategy)

        profit = (vault.totalAssets() - startingBalance).to("ether")
        strState = vault.strategies(strategy)
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
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    i = 0
    while strategy.estimatedTotalAssets() > 1e9:
        i = i +1
        strategy.harvest({"from": gov})
        print("iteration ", i)
        stateOfStrat(strategy, dai, comp)
        
    stateOfStrat(strategy, dai, comp)
    stateOfVault(vault, strategy)