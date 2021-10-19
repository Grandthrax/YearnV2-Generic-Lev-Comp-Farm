from utils import actions, checks, utils
import pytest


def test_airdrop(
    chain,
    accounts,
    token,
    vault,
    strategy,
    user,
    strategist,
    amount,
    RELATIVE_APPROX,
    token_whale,
):
    # Deposit to the vault
    actions.user_deposit(user, vault, token, amount)

    # Harvest 1: Send funds through the strategy
    chain.sleep(1)
    strategy.harvest({"from": strategist})
    total_assets = strategy.estimatedTotalAssets()
    assert pytest.approx(total_assets, rel=RELATIVE_APPROX) == amount

    # we airdrop tokens to strategy
    airdrop_amount = amount * 0.1  # 10% of current assets
    token.transfer(strategy, airdrop_amount, {"from": token_whale})

    # check that estimatedTotalAssets estimates correctly
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=1e-3)
        == total_assets + airdrop_amount
    )

    before_pps = vault.pricePerShare()
    # Harvest 2: Realize profit
    chain.sleep(1)
    strategy.harvest()

    utils.sleep()

    profit = token.balanceOf(vault.address)  # Profits go to vault
    assert vault.strategies(strategy).dict()["totalDebt"] + profit > amount
    assert vault.pricePerShare() > before_pps
