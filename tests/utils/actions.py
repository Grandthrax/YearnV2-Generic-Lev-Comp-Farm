import pytest
from brownie import chain
import utils

# This file is reserved for standard actions like deposits
def user_deposit(user, vault, token, amount):
    print(f"Depositing {amount / 10 ** token.decimals()} {token.symbol()} from {user.address}")
    if token.allowance(user, vault) < amount:
        token.approve(vault, 2 ** 256 - 1, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount


# TODO: add args as required
def generate_profit(strategy, blocks_sleep):
    # setting min comp to sell to 0 to ensure that we sell it (even if not gas efficient)
    print(f"Generating profit for {blocks_sleep} blocks")
    strategy.setMinCompToSell(0, {'from': strategy.strategist()})
    total_assets_start = strategy.estimatedTotalAssets()
    chain.sleep(int(blocks_sleep * 13.15))
    chain.mine(blocks_sleep)
    strategy.getLivePosition() # to update
    total_assets_end = strategy.estimatedTotalAssets()   
    return total_assets_end - total_assets_start


# TODO: add args as required
def generate_loss(strategy):
    print(f"Generating loss")
    supply, borrow = strategy.getCurrentPosition()
    total_assets_start = supply - borrow
    theo_lent = borrow * 1e18 / (strategy.collateralTarget() + 1e18)
    
    cToken = Contract(strategy.cToken())
    drop_amount = supply - theo_lent
    cToken.transfer(strategy.strategist(), drop_amount, {'from': strategy})

    strategy.getLivePosition() # to update
    supply, borrow = strategy.getCurrentPosition()
    total_assets_end = supply - borrow
    return total_assets_start - total_assets_end


def first_deposit_and_harvest(
    vault, strategy, token, user, gov, amount, RELATIVE_APPROX
):
    print(f"Depositing {amount / 10 ** token.decimals()} from {user.address}")
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(8 * 3600)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

def big_deposit_and_harvest(
    vault, strategy, token, user, gov, amount, RELATIVE_APPROX
):
    print(f"Depositing {100 * amount / 10 ** token.decimals()} from {user.address}")
    # Deposit 100x amount to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount * 100, {"from": user})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(8 * 3600)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount


