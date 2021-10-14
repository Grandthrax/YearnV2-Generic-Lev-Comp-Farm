from utils import actions, utils

from brownie import Contract
def test_clone(
    vault, strategy, Strategy, token, cToken, pm, factory, amount, gov, user, RELATIVE_APPROX
):
    # send strategy to steady state
    actions.first_deposit_and_harvest(vault, strategy, token, user, gov, amount, RELATIVE_APPROX)

    cloned_strategy = factory.cloneLevComp(
            vault,
            cToken,
            {"from": gov}
    ).return_value
    cloned_strategy = Strategy.at(cloned_strategy)

    # free funds from old strategy
    vault.revokeStrategy(strategy, {'from': gov})
    strategy.harvest({'from': gov})

    # probably need to harvest again to return funds
    while strategy.estimatedTotalAssets() > strategy.minWant():
        strategy.setDoHealthCheck(False, {'from': gov})
        strategy.harvest({'from': gov})
        utils.sleep(1)
    assert strategy.estimatedTotalAssets() < strategy.minWant()

    vault.addStrategy(cloned_strategy, 10_000, 0, 2**256 - 1, 0, {'from': gov})
    # take funds to new strategy
    cloned_strategy.harvest({'from': gov})
    assert cloned_strategy.estimatedTotalAssets() > 0
