from itertools import count
from brownie import Wei, reverts
from useful_methods import (
    stateOfStrat,
    genericStateOfStrat,
    stateOfVault,
    deposit,
    wait,
    withdraw,
    harvest,
    assertCollateralRatio,
)
import brownie


def test_collat_zero(
    web3, chain, comp, vault, enormousrunningstrategy, whale, gov, dai, strategist
):
    stateOfStrat(enormousrunningstrategy, dai, comp)
    stateOfVault(vault, enormousrunningstrategy)
    enormousrunningstrategy.setMinCompToSell(0, {"from": gov})

    enormousrunningstrategy.setCollateralTarget(0, {"from": gov})
    enormousrunningstrategy.setMinWant(1e18, {"from": gov})
    lastCollat = enormousrunningstrategy.storedCollateralisation()
    strState = vault.strategies(enormousrunningstrategy)
    loss_before = strState[7]
    print(loss_before/1e18)
    while enormousrunningstrategy.storedCollateralisation() > 0.05 * 1e18:
        enormousrunningstrategy.harvest({"from": gov})
        newCollat = enormousrunningstrategy.storedCollateralisation()
        #assert lastCollat > newCollat
        lastCollat = newCollat
        stateOfStrat(enormousrunningstrategy, dai, comp)
        stateOfVault(vault, enormousrunningstrategy)

    enormousrunningstrategy.setEmergencyExit({"from": gov})
    enormousrunningstrategy.harvest({"from": gov})

    stateOfStrat(enormousrunningstrategy, dai, comp)
    genericStateOfStrat(enormousrunningstrategy, dai, vault)
    stateOfVault(vault, enormousrunningstrategy)
    strState = vault.strategies(enormousrunningstrategy)
    # losses == 0 with elegent big withdrawal
    assert strState[7] == loss_before


def test_huge_withdrawal(
    web3, chain, comp, vault, enormousrunningstrategy, whale, gov, dai, strategist
):
    stateOfStrat(enormousrunningstrategy, dai, comp)
    stateOfVault(vault, enormousrunningstrategy)
    #enormousrunningstrategy.setAave(True, {'from': strategist})
    print("\nwhale withdraws")
    vault.withdraw({"from": whale})
    
    stateOfStrat(enormousrunningstrategy, dai, comp)
    genericStateOfStrat(enormousrunningstrategy, dai, vault)
    stateOfVault(vault, enormousrunningstrategy)

    enormousrunningstrategy.harvest({"from": gov})


def test_enourmous_exit(
    web3, chain, comp, vault, enormousrunningstrategy, whale, gov, dai, strategist
):
    stateOfStrat(enormousrunningstrategy, dai, comp)
    stateOfVault(vault, enormousrunningstrategy)
    strState = vault.strategies(enormousrunningstrategy)
    starting_loss = strState[7]
    enormousrunningstrategy.setMinCompToSell(0, {"from": gov})

    enormousrunningstrategy.setEmergencyExit({"from": gov})
    assert enormousrunningstrategy.emergencyExit()

    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    ## emergency shutdown

    enormousrunningstrategy.harvest({"from": gov})
    stateOfStrat(enormousrunningstrategy, dai, comp)
    genericStateOfStrat(enormousrunningstrategy, dai, vault)
    stateOfVault(vault, enormousrunningstrategy)
    strState = vault.strategies(enormousrunningstrategy)
    assert strState[7] < starting_loss*1.01  # loss 0
    assert strState[5] > 0  # debt > 0

    enormousrunningstrategy.harvest({"from": gov})
    enormousrunningstrategy.harvest({"from": gov})
    enormousrunningstrategy.harvest({"from": gov})
    stateOfStrat(enormousrunningstrategy, dai, comp)
    genericStateOfStrat(enormousrunningstrategy, dai, vault)
    stateOfVault(vault, enormousrunningstrategy)
    strState = vault.strategies(enormousrunningstrategy)
    assert strState[5] < 1*1e18  # debt > 0
