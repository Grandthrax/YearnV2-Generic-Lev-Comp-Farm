from brownie import Contract


def test_rewards(vault, strategy, currency, user, gov, chain, comp, whale):
    currency.approve(vault, 2 ** 256 - 1, {'from': user})
    currency.transfer(user, 200e8, {'from': whale})

    # huge deposit to get nice fat rewards
    vault.deposit({'from': user})

    # lever up
    strategy.harvest({'from': gov})

    deposits, borrows = strategy.getCurrentPosition()
    collat = borrows/deposits

    while(collat < (strategy.collateralTarget()-1e15)/1e18):
        strategy.harvest({'from': gov})
        deposits, borrows = strategy.getCurrentPosition()
        collat = borrows/deposits
        print(f"New Collat {collat}")

    chain.sleep(2000*13)
    chain.mine(2000+1)

    prediction = strategy.predictCompAccrued()
    assert prediction > 0

    # claim from strategy
    compound = Contract("0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B")
    compound.claimComp(strategy, {'from': strategy})
    assert comp.balanceOf(strategy)*1.01 > prediction
    chain.undo()
    tx = strategy.harvest({'from': gov})

    # received rewards
    assert tx.events["DistributedSupplierComp"]
    assert tx.events["DistributedBorrowerComp"]
    # a swap happened
    assert tx.events["Swap"]
    # reported profit correctly
    assert tx.events["Harvested"]["profit"] > 0

    print(tx.events)
