
def test_regular_deleverage(vault, big_strategy, user, gov, chain, currency):
    strategy = big_strategy

    vault.updateStrategyDebtRatio(big_strategy, 0, {'from': gov})
    strategy.harvest({'from': gov})

    deposits, borrows = strategy.getCurrentPosition()

    while(deposits > 1e3):
        strategy.harvest({'from': gov})
        deposits, borrows = strategy.getCurrentPosition()

    # one more harvest to get the debt back to the vault
    strategy.harvest({'from': gov}) 

    assert deposits < 1e3
    assert vault.strategies(strategy).dict()['totalDebt'] < 1e3

def test_manual_deleverage(vault, big_strategy, user, gov, chain, currency):
    strategy = big_strategy

    vault.updateStrategyDebtRatio(big_strategy, 0, {'from': gov})

    deposits, borrows = strategy.getCurrentPosition()
    while borrows > 1e3:
        delev_amount = deposits - borrows/0.6425
        if delev_amount > 0:
            strategy.manualDeleverage(min(delev_amount, borrows), {'from': gov})
        else:
            print("oops")
        deposits, borrows = strategy.getCurrentPosition()
        print("New collat: ", borrows/deposits)

    strategy.manualReleaseWant(deposits, {'from': gov})

    strategy.harvest({'from': gov})

    deposits, borrows = strategy.getCurrentPosition()
    assert deposits < 1e3
    assert vault.strategies(strategy).dict()['totalDebt'] < 1e3