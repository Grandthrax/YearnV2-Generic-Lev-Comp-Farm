import pytest
from utils import checks, actions, utils

# TODO: Add tests that show proper operation of this strategy through "emergencyExit"
#       Make sure to demonstrate the "worst case losses" as well as the time it takes


def test_shutdown(chain, token, vault, strategy, amount, gov, user, RELATIVE_APPROX):
    # Deposit to the vault and harvest
    actions.user_deposit(user, vault, token, amount)
    chain.sleep(1)
    strategy.harvest({"from": gov})
    utils.sleep()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # Generate profit
    actions.generate_profit(strategy, 50)

    # Set debtRatio to 0, then harvest, check that accounting worked as expected
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.harvest({"from": gov})
    utils.sleep()

    # TODO: manually do the accounting, then add here and let the code check
    totalGain = profit_amount
    totalLoss = 0
    totalDebt = amount
    checks.check_accounting(vault, strategy, totalGain, totalLoss, totalDebt)
