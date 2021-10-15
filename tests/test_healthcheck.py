from utils import actions
import brownie
from brownie import Contract
import pytest

def test_healthcheck(user, vault, token, amount, strategy, chain, strategist, gov):
    # Deposit to the vault
    actions.user_deposit(user, vault, token, amount)

    assert strategy.doHealthCheck() == False
    assert strategy.healthCheck() == "0x0000000000000000000000000000000000000000"

    strategy.setHealthCheck("0xDDCea799fF1699e98EDF118e0629A974Df7DF012", {'from': gov})
    assert strategy.healthCheck() == "0xDDCea799fF1699e98EDF118e0629A974Df7DF012"
    chain.sleep(1)
    strategy.harvest({"from": strategist})

    chain.sleep(24 * 3600)
    chain.mine()

    strategy.setDoHealthCheck(True, {"from": gov})

    loss_amount = actions.generate_loss(strategy)
    # Harvest should revert because the loss in unacceptable
    with brownie.reverts("!healthcheck"):
        strategy.harvest({"from": strategist})

    # we disable the healthcheck
    strategy.setDoHealthCheck(False, {"from": gov})

    # the harvest should go through, taking the loss
    tx = strategy.harvest({"from": strategist})
    assert pytest.approx(tx.events["Harvested"]["loss"], rel=1e-3) == loss_amount

    vault.withdraw({"from": user})
    assert token.balanceOf(user) < amount  # user took losses
