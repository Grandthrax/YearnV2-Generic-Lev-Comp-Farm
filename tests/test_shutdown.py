import pytest
from utils import checks, actions, utils

# TODO: Add tests that show proper operation of this strategy through "emergencyExit"
#       Make sure to demonstrate the "worst case losses" as well as the time it takes


def test_shutdown(chain, token, vault, strategy, amount, gov, user, RELATIVE_APPROX):
    # Deposit to the vault and harvest
    actions.user_deposit(user, vault, token, amount)
    chain.sleep(1)
    strategy.harvest({"from": gov})
    utils.sleep(1)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # Generate profit
    profit_amount = actions.generate_profit(strategy, 50)

    # Set debtRatio to 0, then harvest, check that accounting worked as expected
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.harvest({"from": gov})
    utils.sleep(1)
    strategy.harvest({"from": gov})
    utils.sleep()

    status = vault.strategies(strategy).dict()
    assert status["totalGain"] >= profit_amount # underestimating
    assert pytest.approx(status["totalLoss"], abs=strategy.minWant()) == 0
    assert pytest.approx(status["totalDebt"], abs=strategy.minWant()) == 0

