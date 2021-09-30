from brownie import Contract, accounts
from useful_methods import stateOfStrat

def test_live_juan(chain):
    strategy = Contract("0x83B6211379c26E0bA8d01b9EcD4eE1aE915630aa")
    vault_weth = Contract(strategy.vault())
    gov = accounts.at(vault_weth.governance(), force=True)
    weth = Contract(strategy.want())
    comp = Contract("0xc00e94Cb662C3520282E6f5717214004A7f26888")
    desired = 10_000 - vault_weth.debtRatio()
    # vault_weth.addStrategy(strategy, desired, 0, 2**256-1, 1000, {'from': gov})
    vault_weth.updateStrategyDebtRatio(strategy, desired, {'from': gov})

    tx = strategy.harvest({'from': gov})
    deposits, borrows = strategy.getCurrentPosition()
    print("0 borrows, deposits", borrows, deposits)
    print(deposits/vault_weth.strategies(strategy).dict()['totalDebt'])
    while(borrows/deposits < 0.73):
        tx = strategy.harvest({'from': gov})
        
        deposits, borrows = strategy.getCurrentPosition()
        print("borrows, deposits", borrows, deposits)
        print(deposits/vault_weth.strategies(strategy).dict()['totalDebt'])

    print("Reached 3.7x leverage")
    
    chain.sleep(10 * 24 * 3600)
    chain.mine(1500)

    vault_weth.updateStrategyDebtRatio(strategy, 0, {'from': gov})
    print("preDebt", vault_weth.strategies(strategy).dict()['totalDebt'])
    stateOfStrat(strategy, weth, comp)
    tx = strategy.harvest({'from': gov})
    stateOfStrat(strategy, weth, comp)

    deposits, borrows = strategy.getCurrentPosition()
    print("0 borrows, deposits", borrows, deposits)
    print(deposits/vault_weth.strategies(strategy).dict()['totalDebt'])
    while(deposits > 1e10):
        if borrows < 1e7:
            strategy.setCollateralTarget(0, {'from': gov})
            strategy.setDyDx(False, {'from': gov})
            strategy.setDoHealthCheck(False, {'from': gov})
        tx = strategy.harvest({'from': gov})
        
        deposits, borrows = strategy.getCurrentPosition()
        print("borrows, deposits", borrows, deposits)
        print(deposits/vault_weth.strategies(strategy).dict()['totalDebt'])

    print(vault_weth.strategies(strategy).dict()['totalDebt'])
    