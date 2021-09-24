import pytest
from brownie import Contract, accounts
# deposit 1 WBTC and leverage it according to the collateralTarget
def test_simple(vault, strategy, currency, comp, user, gov, chain):
    chain.snapshot()
    strategy = Contract("0x4F3c19878da5366fd85648Ef8692D96067dEE16D")

    vault = Contract(strategy.vault())
    gov = accounts.at(vault.governance(), force=True)
    strategy.setHealthCheck('0xDDCea799fF1699e98EDF118e0629A974Df7DF012', {'from': gov})

    vault.addStrategy(strategy, 1000, 0, 2**256-1, 1000, {'from': gov})

    currency.approve(vault, 2 ** 256 - 1, {'from': user})
    vault.deposit(1e8, {'from': user})
    gov.transfer(strategy, 100000)
    strategy.harvest({'from': gov})

    deposits, borrows = strategy.getCurrentPosition()
    collat = borrows/deposits

    while(collat < (strategy.collateralTarget()-1e15)/1e18):
        strategy.harvest({'from': gov})
        deposits, borrows = strategy.getCurrentPosition()
        collat = borrows/deposits
        print(f"New Collat {collat}")

    real_assets = deposits - borrows
    assert pytest.approx(real_assets, rel=1e-3) == vault.strategies(strategy).dict()['totalDebt']
    assert deposits/real_assets == pytest.approx(2.70, rel=1e-2) # 2.7x leverage

    chain.sleep(1500 * 13)
    chain.mine(1500)

    # debt ratio to 0
    vault.updateStrategyDebtRatio(strategy, 0, {'from': gov})

    # first harvest will be needed for sure
    strategy.harvest({'from': gov})
    deposits, borrows = strategy.getCurrentPosition()
    while(deposits > 1e3):
        deposits, borrows = strategy.getCurrentPosition()
        strategy.harvest({'from': gov})

    # one more harvest to get the debt back to the vault
    strategy.harvest({'from': gov}) 
    assert vault.strategies(strategy).dict()['totalDebt'] < 1e3
    chain.revert()
def test_huge_deposit(vault, strategy, currency, user, chain, gov):
    chain.snapshot()
    strategy = Contract("0x4F3c19878da5366fd85648Ef8692D96067dEE16D")
    vault = Contract(strategy.vault())
    gov = accounts.at(vault.governance(), force=True)
    strategy.setHealthCheck('0xDDCea799fF1699e98EDF118e0629A974Df7DF012', {'from': gov})
    vault.addStrategy(strategy, 1000, 0, 2**256-1, 1000, {'from': gov})
    gov.transfer(strategy, 100000)

    currency.approve(vault, 2 ** 256 - 1, {'from': user})
    vault.deposit(3500e8, {'from': user})

    strategy.harvest({'from': gov})
    deposits, borrows = strategy.getCurrentPosition()
    collat = borrows/deposits

    while(collat < (strategy.collateralTarget()-1e15)/1e18):
        strategy.harvest({'from': gov})
        deposits, borrows = strategy.getCurrentPosition()
        collat = borrows/deposits
        print(f"New Collat {collat}")

    real_assets = deposits - borrows
    assert real_assets == pytest.approx(vault.strategies(strategy).dict()['totalDebt'], rel=1e-2)
    assert deposits/real_assets == pytest.approx(2.70, rel=1e-2) # 2.7x leverage

    print("Sleeping and mining some blocks")
    chain.sleep(10 * 24 * 3600)
    chain.mine(1500)

    # to avoid mining more blocks until it reaches default value
    strategy.setMinCompToSell(1e10, {'from': gov})
    # debt ratio to 0
    vault.updateStrategyDebtRatio(strategy, 0, {'from': gov})

    # first harvest will be needed for sure
    strategy.harvest({'from': gov})
    deposits, borrows = strategy.getCurrentPosition()
    while(deposits > 1e3):
        deposits, borrows = strategy.getCurrentPosition()
        strategy.harvest({'from': gov})

    # last harvest to return
    strategy.harvest({'from': gov})

    assert vault.strategies(strategy).dict()['totalDebt'] < 1e3
    chain.revert()