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


def test_deleverage_without_flashloans(
    web3,
    chain,
    comp,
    vault_usdc,
    enormousrunningstrategy_usdc,
    whale,
    gov,
    usdc,
    strategist,
):
    strategy = enormousrunningstrategy_usdc
    vault = vault_usdc
    currency = usdc
    stateOfStrat(strategy, currency, comp)

    strategy.setDyDx(False, {"from": strategist})
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})

    strategy.harvest({"from": strategist})
    stateOfStrat(strategy, currency, comp)
    strategy.harvest({"from": strategist})
    stateOfStrat(strategy, currency, comp)
    strategy.harvest({"from": strategist})
    stateOfStrat(strategy, currency, comp)
    strategy.harvest({"from": strategist})
    stateOfStrat(strategy, currency, comp)
    strategy.harvest({"from": strategist})
    stateOfStrat(strategy, currency, comp)
    strategy.harvest({"from": strategist})
    stateOfStrat(strategy, currency, comp)
