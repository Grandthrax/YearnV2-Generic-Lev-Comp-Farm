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

def test_health_check(
    web3, chain, comp, vault, largerunningstrategy, whale, gov, dai, strategist, health_check, accounts
):
    hgov = accounts.at(health_check.governance(), force=True)
    health_check.setlossLimitRatio(0, {"from": hgov})
    #set comp high 
    largerunningstrategy.setMinCompToSell(1_000*1e18, {"from": gov})
    chain.mine(10)
    with brownie.reverts('!healthcheck'):
        largerunningstrategy.harvest({"from": gov})

    health_check.setlossLimitRatio(1, {"from": hgov})
    largerunningstrategy.harvest({"from": gov})
    stateOfStrat(largerunningstrategy, dai, comp)
    stateOfVault(vault, largerunningstrategy)

    dai.transfer(largerunningstrategy, dai.balanceOf(whale), {'from': whale})
    #should revert
    with brownie.reverts('!healthcheck'):
        largerunningstrategy.harvest({"from": gov})

    largerunningstrategy.setDoHealthCheck(False, {"from": gov})
    largerunningstrategy.harvest({"from": gov})
    

