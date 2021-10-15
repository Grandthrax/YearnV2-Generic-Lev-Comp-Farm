import brownie
from brownie import Contract
import pytest
from utils import actions, checks, utils


def test_large_deleverage_to_zero(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX
):
    # Deposit to the vault and harvest
    actions.user_deposit(user, vault, token, amount)
    utils.sleep(1)
    strategy.harvest({"from": strategist})

    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
        == amount
    )

    utils.sleep(4 * 3600)
    chain.mine(1000)

    utils.strategy_status(vault, strategy)

    vault.revokeStrategy(strategy.address, {"from": gov})
    n = 0
    while vault.debtOutstanding(strategy) > strategy.minWant() and n < 6:
        utils.sleep(1)
        print(f"Iteration: {n}")
        strategy.harvest({"from": strategist})
        utils.strategy_status(vault, strategy)
        n += 1

    utils.sleep()
    utils.strategy_status(vault, strategy)
    assert (
        pytest.approx(
            vault.strategies(strategy).dict()["totalLoss"], abs=strategy.minWant()
        )
        == 0
    )


def test_large_deleverage_parameter_change(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX
):
    # Deposit to the vault and harvest
    actions.user_deposit(user, vault, token, amount)
    utils.sleep(1)
    strategy.harvest({"from": strategist})

    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
        == amount
    )

    utils.sleep(4 * 3600)
    chain.mine(1000)

    strategy.setCollateralTarget(
        strategy.collateralTarget() / 2,
        {"from": gov},
    )

    utils.strategy_status(vault, strategy)

    n = 0
    while (
        not pytest.approx(strategy.storedCollateralisation(), rel=1e-3)
        == strategy.collateralTarget()
    ):
        utils.sleep(1)
        strategy.harvest({"from": strategist})
        utils.strategy_status(vault, strategy)
        n += 1

    print(f"Achieved right collat ratio")

    assert (
        pytest.approx(strategy.storedCollateralisation(), rel=1e-3)
        == strategy.collateralTarget()
    )
    utils.sleep()
    utils.strategy_status(vault, strategy)
    assert (
        pytest.approx(
            vault.strategies(strategy).dict()["totalLoss"], abs=strategy.minWant()
        )
        == 0
    )


def test_large_manual_deleverage_to_zero(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX
):
    # Deposit to the vault and harvest
    actions.user_deposit(user, vault, token, amount)
    utils.sleep(1)
    strategy.harvest({"from": strategist})
    # to realise profits
    strategy.setMinCompToSell(0, {'from': gov})
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
        == amount
    )

    chain.sleep(4 * 3600)
    chain.mine(1000)

    strategy.harvest({'from': strategist})
    utils.strategy_status(vault, strategy)

    (supply, borrow) = strategy.getCurrentPosition()

    n = 0
    while borrow > 100:
        utils.sleep(1)
        (supply, borrow) = strategy.getCurrentPosition()
        theo_min_supply = borrow / (((strategy.collateralTarget() + 1.8*1e16) / 1e18))
        step_size = min(int(supply - theo_min_supply), borrow)
        print(f"Iteration {n}")
        print(f"Supply: {supply / 10 ** token.decimals()}")
        print(f"Borrow: {borrow / 10 ** token.decimals()}")
        print(f"StepSize: {step_size / 10 ** token.decimals()}")
        strategy.manualDeleverage(step_size, {"from": gov})

        n += 1
        (supply, borrow) = strategy.getCurrentPosition()

    utils.strategy_status(vault, strategy)
    print(f"manualDeleverage calls: {n} iterations")

    utils.sleep(1)
    deposits = strategy.getCurrentPosition().dict()["deposits"]
    strategy.manualReleaseWant(deposits, {"from": gov})
    deposits = strategy.getCurrentPosition().dict()["deposits"]
    strategy.manualReleaseWant(deposits, {"from": gov})
    assert strategy.getCurrentPosition().dict()["deposits"] <= strategy.minWant()

    utils.sleep()
    utils.strategy_status(vault, strategy)
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
        == amount
    ) or strategy.estimatedTotalAssets() > amount

    vault.revokeStrategy(strategy.address, {"from": gov})
    strategy.harvest({"from": strategist})
    if strategy.estimatedTotalAssets() > strategy.minWant(): 
        strategy.harvest({'from': strategist})
    utils.strategy_status(vault, strategy)
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), abs=strategy.minWant()) == 0
    )
