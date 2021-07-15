
def test_simple(vault, strategy, currency, comp, user, gov):
    currency.approve(vault, 2 ** 256 - 1, {'from': user})
    vault.deposit({'from': user})
    
    strategy.harvest({'from': gov})
    assert False