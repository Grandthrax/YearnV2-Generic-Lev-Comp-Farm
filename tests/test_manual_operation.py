from utils import actions
from utils import utils
import pytest


# TODO: check that all manual operation works as expected
# manual operation: those functions that are called by management to affect strategy's position
# e.g. repay debt manually
# e.g. emergency unstake
def test_manual_function1(
    chain, token, vault, strategy, amount, gov, user, management, RELATIVE_APPROX
):
    # set up steady state
    actions.first_deposit_and_harvest(
        vault, strategy, token, user, gov, amount, RELATIVE_APPROX
    )

    # use manual function
    # test manual deleverage
    (supply, borrow) = strategy.getCurrentPosition()
    theo_min_supply = borrow / ((strategy.collateralTarget() + 1e18) / 1e18)
    step_size = min(int(supply - theo_min_supply), borrow)
    strategy.manualDeleverage(step_size, {"from": gov})
    (supply_end, borrow_end) = strategy.getCurrentPosition()
    assert pytest.approx(supply - step_size, rel=1e-3) == supply_end
    assert pytest.approx(borrow - step_size, rel=1e-3) == borrow_end
    # test manual release want
    (supply, borrow) = strategy.getCurrentPosition()
    theo_min_supply = borrow / ((strategy.collateralTarget() + 1e18) / 1e18)
    step_size = min(int(supply - theo_min_supply), borrow)
    strategy.manualReleaseWant(step_size, {"from": gov})
    (supply_end, borrow_end) = strategy.getCurrentPosition()
    assert pytest.approx(supply - step_size, rel=1e-3) == supply_end
    assert borrow == borrow_end

    # shut down strategy and check accounting
    strategy.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.harvest({"from": gov})
    utils.sleep()
    return
