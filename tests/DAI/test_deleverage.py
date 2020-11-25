from itertools import count
from brownie import Wei, reverts
from useful_methods import stateOfStrat, genericStateOfStrat, stateOfVault, deposit,wait, withdraw, harvest,assertCollateralRatio
import brownie

def test_collat_zero(web3, chain, comp, vault, enormousrunningstrategy, whale, gov, dai, strategist):
    stateOfStrat(enormousrunningstrategy, dai, comp)
    stateOfVault(vault, enormousrunningstrategy)

    enormousrunningstrategy.setCollateralTarget(0, {"from": gov})
    lastCollat = enormousrunningstrategy.storedCollateralisation()
    while enormousrunningstrategy.storedCollateralisation() > 0.05*1e18:
        enormousrunningstrategy.harvest({"from": gov})
        newCollat = enormousrunningstrategy.storedCollateralisation() 
        assert lastCollat> newCollat
        lastCollat= newCollat
        stateOfStrat(enormousrunningstrategy, dai, comp)
        stateOfVault(vault, enormousrunningstrategy)

def test_huge_withdrawal(web3, chain, comp, vault, enormousrunningstrategy, whale, gov, dai, strategist):
    stateOfStrat(enormousrunningstrategy, dai, comp)
    stateOfVault(vault, enormousrunningstrategy)

    enormousrunningstrategy.setCollateralTarget(0, {"from": gov})
    lastCollat = enormousrunningstrategy.storedCollateralisation()
    while enormousrunningstrategy.storedCollateralisation() > 0.05*1e18:
        enormousrunningstrategy.harvest({"from": gov})
        newCollat = enormousrunningstrategy.storedCollateralisation() 
        assert lastCollat> newCollat
        lastCollat= newCollat
        stateOfStrat(enormousrunningstrategy, dai, comp)
        stateOfVault(vault, enormousrunningstrategy)

    enormousrunningstrategy.setEmergencyExit({"from": gov})
    enormousrunningstrategy.harvest({'from': gov})

    stateOfStrat(enormousrunningstrategy, dai, comp)
    genericStateOfStrat(enormousrunningstrategy, dai, vault)
    stateOfVault(vault, enormousrunningstrategy)
    strState = vault.strategies(enormousrunningstrategy)
    #losses == 0 with elegent big withdrawal
    assert strState[7] == 0


def test_enourmous_exit(web3, chain, comp, vault, enormousrunningstrategy, whale, gov, dai, strategist):
    stateOfStrat(enormousrunningstrategy, dai, comp)
    stateOfVault(vault, enormousrunningstrategy)

    enormousrunningstrategy.setEmergencyExit({"from": gov})
    assert enormousrunningstrategy.emergencyExit()

    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    ## emergency shutdown 

    enormousrunningstrategy.harvest({'from': gov})
    stateOfStrat(enormousrunningstrategy, dai, comp)
    genericStateOfStrat(enormousrunningstrategy, dai, vault)
    stateOfVault(vault, enormousrunningstrategy)
    strState = vault.strategies(enormousrunningstrategy)
    assert strState[7] > 0

