from utils import actions, checks, utils
import pytest

# tests harvesting a strategy that returns profits correctly
def test_profitable_harvest(
    chain, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX
):
    # Deposit to the vault
    actions.user_deposit(user, vault, token, amount)

    # Harvest 1: Send funds through the strategy
    chain.sleep(1)
    strategy.harvest({"from": strategist})
    total_assets = strategy.estimatedTotalAssets()
    assert pytest.approx(total_assets, rel=RELATIVE_APPROX) == amount

    blocks_to_sleep = 50
    profit_amount = actions.generate_profit(strategy, blocks_to_sleep)
    strategy.setMinCompToSell(1e3)
    # check that estimatedTotalAssets estimates correctly
    assert total_assets + profit_amount == strategy.estimatedTotalAssets()

    before_pps = vault.pricePerShare()
    # Harvest 2: Realize profit
    chain.sleep(1)
    tx = strategy.harvest({"from": strategist})
    # profit amount is understimated on purpose
    # checks.check_harvest_profit(tx, profit_amount)

    utils.sleep()
    profit = token.balanceOf(vault.address)  # Profits go to vault

    assert vault.strategies(strategy).dict()["totalDebt"] + profit > amount
    assert vault.pricePerShare() > before_pps

    vault.withdraw({"from": user})


# tests harvesting a strategy that reports losses
def test_lossy_harvest(
    chain, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX
):
    # Deposit to the vault
    actions.user_deposit(user, vault, token, amount)

    # Harvest 1: Send funds through the strategy
    chain.sleep(1)
    strategy.harvest({"from": strategist})
    total_assets = strategy.estimatedTotalAssets()
    assert pytest.approx(total_assets, rel=RELATIVE_APPROX) == amount

    print(f"{strategy.getCurrentPosition().dict()}")
    loss_amount = actions.generate_loss(strategy)
    print(f"{strategy.getCurrentPosition().dict()}")
    print(f"Total loss: {loss_amount}")
    # check that estimatedTotalAssets estimates correctly
    supply, borrow = strategy.getCurrentPosition()
    assert pytest.approx(total_assets - loss_amount, rel=1e-3) == supply - borrow

    # Harvest 2: Realize loss
    chain.sleep(1)
    tx = strategy.harvest({"from": strategist})
    checks.check_harvest_loss(tx, loss_amount)

    utils.sleep()

    # User will withdraw accepting losses
    vault.withdraw(vault.balanceOf(user), user, 10_000, {"from": user})
    assert pytest.approx(token.balanceOf(user) + loss_amount, rel=1e-3) == amount


# tests harvesting a strategy twice, once with loss and another with profit
# it checks that even with previous profit and losses, accounting works as expected
def test_choppy_harvest(
    chain, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX
):
    # Deposit to the vault
    actions.user_deposit(user, vault, token, amount)

    # Harvest 1: Send funds through the strategy
    chain.sleep(1)
    strategy.harvest({"from": strategist})

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    loss_amount = actions.generate_loss(strategy)

    # Harvest 2: Realize loss
    chain.sleep(1)
    tx = strategy.harvest({"from": strategist})
    # TODO: bring back checks
    # checks.check_harvest_loss(tx, loss_amount)

    previous_profit = (
        strategy.estimatedTotalAssets() - vault.strategies(strategy).dict()["totalDebt"]
    )

    blocks_to_sleep = 100
    profit_amount = actions.generate_profit(strategy, blocks_to_sleep)

    chain.sleep(1)
    tx = strategy.harvest({"from": strategist})
    # checks.check_harvest_profit(tx, profit_amount + previous_profit)

    utils.sleep()

    # User will withdraw accepting losses
    vault.withdraw(vault.balanceOf(user), user, 10_000, {"from": user})

    # User will take 100% losses and 100% profits
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX)
        == amount
        + tx.events["StrategyReported"]["totalGain"]
        - tx.events["StrategyReported"]["totalLoss"]
    )
