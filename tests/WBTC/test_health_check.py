import brownie 

def test_health_check(vault, strategy, currency, comp, user, gov, chain, whale):
    currency.approve(vault, 2 ** 256 - 1, {'from': user})
    vault.deposit(1e8, {'from': user})
    
    chain.sleep(1)
    chain.mine()
    strategy.harvest({'from': gov})

    # no losses allowed
    healthcheck = brownie.Contract(strategy.healthCheck())
    healthcheck.setlossLimitRatio(0, {'from': gov})

    chain.mine(100) # mine 100 blocks to incur into debt > assets

    with brownie.reverts("!healthcheck"):
        strategy.harvest({'from': gov})

    # throw big profit
    currency.transfer(strategy, 10e8, {'from': whale})

    with brownie.reverts("!healthcheck"):
        strategy.harvest({'from': gov})

    strategy.setDoHealthCheck(False, {'from': gov})

    tx = strategy.harvest({'from': gov})
    assert tx.events['Harvested']['profit'] > 1e8