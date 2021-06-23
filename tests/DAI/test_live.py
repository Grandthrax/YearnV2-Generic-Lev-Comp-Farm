from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import (
    genericStateOfStrat,
    wait,
    withdraw,
    stateOfVault,
    stateOfStrat,
    genericStateOfVault,
    deposit,
    tend,
    sleep,
    harvest,
)
import random
import brownie


def test_snapshot_both(
    live_vault_dai_030,
    live_strategy_dai_030,
    live_vault_usdc_030,
    live_strategy_usdc_030,
    Contract,
    whale,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    usdc,
    currency,
    samdev,
):
    strategist = samdev
    strategy = live_strategy_dai_030
    vault = live_vault_dai_030
    gov = accounts.at(live_vault_dai_030.governance(), force=True)

    print("\nDAI")
    stateOfStrat(live_strategy_dai_030, dai, comp)
    genericStateOfVault(live_vault_dai_030, dai)
    genericStateOfStrat(live_strategy_dai_030, dai, live_vault_dai_030)

    print("\nUSDC")
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    genericStateOfVault(live_vault_usdc_030, usdc)
    genericStateOfStrat(live_strategy_usdc_030, usdc, live_vault_usdc_030)

def test_add_both(
    live_vault_dai_030,
    live_strategy_dai_030,
    live_strategy_dai_030_2,
    live_vault_usdc_030,
    live_strategy_usdc_030_2,
    Contract,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    usdc,
    currency,
    samdev,
):
    strategist = samdev
    gov = accounts.at(live_vault_dai_030.governance(), force=True)
    ah2 = Contract('0x7D960F3313f3cB1BBB6BF67419d303597F3E2Fa8')
    iblev = Contract('0x77b7CD137Dd9d94e7056f78308D7F65D2Ce68910')

    #live_vault_dai_030.updateStrategyDebtRatio(ah2, 0, {'from':gov})
    #live_vault_dai_030.updateStrategyDebtRatio(live_strategy_dai_030, 0, {'from':gov})
    #live_vault_dai_030.updateStrategyDebtRatio(iblev, 100, {'from':gov})
    #genericStateOfStrat(ah2, dai, live_vault_dai_030)
    #ah2.harvest({"from": gov})
    #genericStateOfStrat(ah2, dai, live_vault_dai_030)
    #live_vault_dai_030.updateStrategyDebtRatio(live_strategy_dai_030_2, 5196, {'from':gov})
    assert live_vault_dai_030.debtRatio() == 10000

    i = 0
    while live_strategy_dai_030.estimatedTotalAssets() > 40*1e18:
        live_strategy_dai_030.harvest({'from':gov})
        stateOfStrat(live_strategy_dai_030, dai, comp)
        i = i + 1
        print(i)
    live_strategy_dai_030_2.setMinCompToSell(1, {"from": gov})

    
    #live_strategy_dai_030_2.harvest({'from':gov})
    #stateOfStrat(live_strategy_dai_030_2, dai, comp)
    #live_strategy_dai_030_2.setDyDx(False, {'from':gov})
    #live_strategy_dai_030_2.setDyDx(True, {'from':gov})
    #live_strategy_dai_030_2.harvest({'from':gov})
    stateOfStrat(live_strategy_dai_030_2, dai, comp)
    #live_strategy_dai_030_2.setDyDx(True, {'from':gov})
    live_strategy_dai_030_2.harvest({'from':gov})
    stateOfStrat(live_strategy_dai_030_2, dai, comp)
    startingAssets = live_strategy_dai_030_2.estimatedTotalAssets()
    startingProfit = live_vault_dai_030.strategies(live_strategy_dai_030_2)[6]
    waitTime = 100
    chain.mine(waitTime)
    chain.sleep(1)
    live_strategy_dai_030_2.harvest({'from':gov})
    profit = live_vault_dai_030.strategies(live_strategy_dai_030_2)[6] - startingProfit
    blocks_per_year = 2_300_000
    apr = (profit/startingAssets) *(blocks_per_year/waitTime)
    print("APR = ", apr)
    #apr is less than 25% and more than 3%
    assert apr < 0.25 and apr > 0.03

    stateOfStrat(live_strategy_dai_030_2, dai, comp)
    genericStateOfStrat(live_strategy_dai_030_2, dai, live_vault_dai_030)

    #emergency exit
    live_vault_dai_030.updateStrategyDebtRatio(live_strategy_dai_030_2, 0, {'from':gov})
    live_strategy_dai_030_2.harvest({'from': strategist})
    live_strategy_dai_030_2.harvest({'from': strategist})
    stateOfStrat(live_strategy_dai_030_2, dai, comp)
    live_strategy_dai_030_2.harvest({'from': strategist})
    stateOfStrat(live_strategy_dai_030_2, dai, comp)
    live_strategy_dai_030_2.harvest({'from': strategist})
    stateOfStrat(live_strategy_dai_030_2, dai, comp)
    live_strategy_dai_030_2.harvest({'from': strategist})
    stateOfStrat(live_strategy_dai_030_2, dai, comp)
    genericStateOfStrat(live_strategy_dai_030_2, dai, live_vault_dai_030)
    assert live_strategy_dai_030_2.estimatedTotalAssets() < 10*1e18
    

def test_close_both(
    live_vault_dai_030,
    live_strategy_dai_030,
    live_vault_usdc_030,
    live_strategy_usdc_030,
    Contract,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    usdc,
    currency,
    samdev,
):
    strategist = samdev
    strategy = live_strategy_dai_030
    vault = live_vault_dai_030
    gov = accounts.at(live_vault_dai_030.governance(), force=True)
    # live_strategy_dai_030.setDyDx(False, {'from': gov})

    print("\nDAI")
    # vault.updateStrategyDebtRatio(live_strategy_dai_030, 0, {'from': gov})
    # live_strategy_dai_030.harvest({'from': gov})
    # stateOfStrat(live_strategy_dai_030, dai, comp)
    # live_strategy_dai_030.harvest({'from': gov})
    # stateOfStrat(live_strategy_dai_030, dai, comp)
    # live_strategy_dai_030.harvest({'from': gov})
    # stateOfStrat(live_strategy_dai_030, dai, comp)
    # live_strategy_dai_030.harvest({'from': gov})
    # stateOfStrat(live_strategy_dai_030, dai, comp)

    live_strategy_usdc_030.setDyDx(False, {"from": gov})

    print("\nUSDC")
    vault = live_vault_usdc_030
    vault.updateStrategyDebtRatio(live_strategy_usdc_030, 0, {"from": gov})
    live_strategy_usdc_030.setCollateralTarget(0, {"from": gov})
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)
    live_strategy_usdc_030.harvest({"from": gov})
    stateOfStrat(live_strategy_usdc_030, usdc, comp)


def test_deposit_live_dai(
    live_vault_dai_030,
    live_strategy_dai_030,
    Contract,
    whale,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    currency,
    samdev,
):
    strategist = samdev
    strategy = live_strategy_dai_030
    vault = live_vault_dai_030

    stateOfStrat(strategy, currency, comp)
    genericStateOfVault(vault, currency)
    genericStateOfStrat(strategy, currency, vault)

    amount = Wei("499000 ether")
    dai.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})

    strategy.harvest({"from": strategist})
    stateOfStrat(strategy, currency, comp)
    genericStateOfVault(vault, currency)
    genericStateOfStrat(strategy, currency, vault)


def test_deposit_live_usdc(
    live_vault_usdc_030,
    live_strategy_usdc_030,
    Contract,
    whale,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    usdc,
    currency,
    samdev,
):
    strategist = samdev
    strategy = live_strategy_usdc_030
    vault = live_vault_usdc_030
    #  assert vault.governance() != live_gov
    #  vault.acceptGovernance({'from': live_gov})

    stateOfStrat(strategy, usdc, comp)
    genericStateOfVault(vault, usdc)
    genericStateOfStrat(strategy, usdc, vault)
    # print(vault.governance())

    assert vault.governance() == live_gov.address
    amount = 499000 * 1e6
    usdc.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})

    strategy.harvest({"from": strategist})
    stateOfStrat(strategy, usdc, comp)
    genericStateOfVault(vault, usdc)
    genericStateOfStrat(strategy, usdc, vault)


def test_live_apr_usdc(
    live_vault_usdc_030,
    live_strategy_usdc_030,
    Contract,
    whale,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    usdc,
    currency,
    samdev,
):
    strategist = samdev
    strategy = live_strategy_usdc_030
    vault = live_vault_usdc_030
    strategy.setMinCompToSell(0, {"from": strategist})

    strategy.harvest({"from": strategist})
    startingBalance = vault.totalAssets()

    for i in range(6):

        waitBlock = 500
        print(f"\n----wait {waitBlock} blocks----")
        wait(waitBlock, chain)
        ppsBefore = vault.pricePerShare()
        print(ppsBefore / 1e6)

        strategy.harvest({"from": strategist})

        # stateOfStrat(strategy, usdc, comp)
        # genericStateOfVault(vault, usdc)

        ppsAfter = vault.pricePerShare()
        print(ppsAfter / 1e6)

        profit = (vault.totalAssets() - startingBalance) / 1e6
        strState = vault.strategies(strategy)
        totalReturns = strState[6]
        totaleth = totalReturns / 1e6
        print(f"Real Profit: {profit:.5f}")
        difff = profit - totaleth
        # print(f'Diff: {difff}')

        blocks_per_year = 2_300_000
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        ppsProfit = (ppsAfter - ppsBefore) / ppsBefore / waitBlock * blocks_per_year
        apr = (profit / (startingBalance / 1e6)) * (blocks_per_year / time)
        print(f"implied apr assets: {apr:.8%}")
        print(f"implied apr pps: {ppsProfit:.8%}")


def test_live_apr_dai(
    live_vault_dai_030,
    live_strategy_dai_030,
    Contract,
    whale,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    usdc,
    currency,
    samdev,
):
    strategist = samdev
    strategy = live_strategy_dai_030
    vault = live_vault_dai_030
    strategy.setMinCompToSell(0, {"from": strategist})

    strategy.harvest({"from": strategist})
    startingBalance = vault.totalAssets()

    for i in range(6):

        waitBlock = 25
        print(f"\n----wait {waitBlock} blocks----")
        wait(waitBlock, chain)
        ppsBefore = vault.pricePerShare()
        print(ppsBefore / 1e18)

        cdai.mint(0, {"from": strategist})
        strategy.harvest({"from": strategist})

        # stateOfStrat(strategy, usdc, comp)
        # genericStateOfVault(vault, usdc)

        ppsAfter = vault.pricePerShare()
        print(ppsAfter / 1e6)

        profit = (vault.totalAssets() - startingBalance) / 1e18
        strState = vault.strategies(strategy)
        totalReturns = strState[6]
        totaleth = totalReturns / 1e18
        print(f"Real Profit: {profit:.5f}")
        difff = profit - totaleth
        # print(f'Diff: {difff}')

        blocks_per_year = 2_300_000
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        ppsProfit = (ppsAfter - ppsBefore) / ppsBefore / waitBlock * blocks_per_year
        apr = (profit / (startingBalance / 1e18)) * (blocks_per_year / time)
        print(f"implied apr assets: {apr:.8%}")
        print(f"implied apr pps: {ppsProfit:.8%}")


def test_screenshot(
    live_vault_dai3,
    live_strategy_dai4,
    Contract,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    live_strategy_dai2,
    currency,
    samdev,
):
    strategist = samdev
    strategy = live_strategy_dai4

    vault = live_vault_dai3

    # vault.revokeStrategy(strategy,{'from': live_gov})

    #  stateOfStrat(strategy, dai, comp)
    #   genericStateOfVault(vault, dai)

    strategy.harvest({"from": strategist})
    strategy.harvest({"from": strategist})

    stateOfStrat(strategy, currency, comp)
    genericStateOfVault(vault, currency)
    genericStateOfStrat(strategy, currency, vault)


def test_screenshot2(
    live_vault_usdc3,
    live_strategy_usdc4,
    usdc,
    Contract,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    live_strategy_dai2,
    currency,
    samdev,
):
    strategist = samdev
    strategy = live_strategy_usdc4

    vault = live_vault_usdc3

    vault.revokeStrategy(strategy, {"from": live_gov})

    #  stateOfStrat(strategy, dai, comp)
    #   genericStateOfVault(vault, dai)
    print(chain.height)

    strategy.harvest({"from": strategist})
    strategy.harvest({"from": strategist})

    stateOfStrat(strategy, usdc, comp)
    genericStateOfVault(vault, usdc)
    genericStateOfStrat(strategy, usdc, vault)


def test_flash_loan(
    live_vault_dai2,
    live_vault_dai3,
    live_strategy_dai3,
    Contract,
    largerunningstrategy,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    live_strategy_dai2,
    currency,
    whale,
    samdev,
):

    vault = live_vault_dai3
    live_strat = live_strategy_dai3

    # aave = Contract.from_explorer('0x398eC7346DcD622eDc5ae82352F02bE94C62d119')
    # malicious call
    # calldata = eth_abi.encode_abi(['bool', 'uint256'], [True, 1000])
    # calldata = eth_abi.encode_single('(bool,uint256)', [True, 1000])
    # print(calldata)
    # aave.flashLoan(live_strat, dai, 100, calldata, {'from': whale})


def test_increase_limit(
    live_vault_dai2,
    live_vault_dai3,
    live_strategy_dai4,
    Contract,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    live_strategy_dai2,
    currency,
    whale,
    samdev,
):

    vault = live_vault_dai3
    strat = live_strategy_dai4
    print(strat)
    print(vault)
    print(vault.availableDepositLimit())
    print(vault.strategies(strat))
    vault.setDepositLimit(525_000 * 1e18, {"from": live_gov})
    vault.updateStrategyDebtLimit(strat, 500_000 * 1e18, {"from": live_gov})

    print(vault.availableDepositLimit())
    print(vault.strategies(strat))


def test_shutdown(
    live_strategy_dai2,
    live_vault_dai2,
    live_strategy_usdc3,
    live_strategy_usdc4,
    live_vault_usdc3,
    live_strategy_dai4,
    Contract,
    usdc,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    currency,
    whale,
    samdev,
):
    stateOfStrat(live_strategy_dai2, dai, comp)
    live_vault_dai2.revokeStrategy(live_strategy_dai2, {"from": samdev})
    stateOfStrat(live_strategy_dai2, dai, comp)

    live_strategy_dai2.harvest({"from": samdev})
    live_strategy_dai2.harvest({"from": samdev})

    stateOfStrat(live_strategy_dai2, dai, comp)
    genericStateOfVault(live_vault_dai2, dai)


def test_migration(
    live_vault_dai3,
    live_strategy_dai3,
    live_strategy_usdc3,
    live_strategy_usdc4,
    live_vault_usdc3,
    live_strategy_dai4,
    Contract,
    usdc,
    web3,
    live_gov,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    live_strategy_dai2,
    currency,
    whale,
    samdev,
):

    vault = live_vault_dai3
    live_strat = live_strategy_dai4
    old_strat = live_strategy_dai3
    stateOfStrat(old_strat, dai, comp)

    vault.migrateStrategy(old_strat, live_strat, {"from": live_gov})

    live_strat.harvest({"from": samdev})
    stateOfStrat(live_strat, dai, comp)

    print("usdc done")
    vault = live_vault_usdc3
    live_strat = live_strategy_usdc4
    old_strat = live_strategy_usdc3
    stateOfStrat(old_strat, usdc, comp)

    vault.migrateStrategy(old_strat, live_strat, {"from": live_gov})

    live_strat.harvest({"from": samdev})
    stateOfStrat(live_strat, usdc, comp)

    # aave = Contract.from_explorer('0x398eC7346DcD622eDc5ae82352F02bE94C62d119')
    # malicious call
    # calldata = eth_abi.encode_abi(['bool', 'uint256'], [True, 1000])
    # calldata = eth_abi.encode_single('(bool,uint256)', [True, 1000])
    # print(calldata)
    # aave.flashLoan(live_strat, dai, 100, calldata, {'from': whale})


def test_add_strat(
    live_vault_dai3,
    Contract,
    usdc,
    web3,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    live_strategy_usdc3,
    live_vault_usdc3,
    live_strategy_dai3,
    live_gov,
    currency,
    whale,
    samdev,
):
    strategist = samdev
    strategy = live_strategy_usdc3
    vault = live_vault_usdc3
    currency = usdc
    gov = live_gov

    stateOfStrat(strategy, currency, comp)
    genericStateOfVault(vault, currency)

    vault.addStrategy(
        strategy,
        2 ** 256 - 1,
        2 ** 256 - 1,
        1000,  # 0.5% performance fee for Strategist
        {"from": gov},
    )

    # amount = Wei('50000 ether')
    # print(dai.balanceOf(whale)/1e18)
    # dai.approve(vault, amount, {'from': whale})
    # vault.deposit(amount, {'from': whale})
    chain.mine(1)

    strategy.harvest({"from": strategist})

    stateOfStrat(strategy, currency, comp)
    genericStateOfVault(vault, currency)
    genericStateOfStrat(strategy, currency, vault)


def test_add_keeper(
    live_vault_dai2,
    Contract,
    web3,
    accounts,
    chain,
    cdai,
    comp,
    dai,
    live_strategy_dai2,
    currency,
    whale,
    samdev,
):
    strategist = samdev
    strategy = live_strategy_dai2
    vault = live_vault_dai2

    # stateOfStrat(strategy, dai, comp)
    # genericStateOfVault(vault, dai)

    keeper = Contract.from_explorer("0x13dAda6157Fee283723c0254F43FF1FdADe4EEd6")

    kp3r = Contract.from_explorer("0x1cEB5cB57C4D4E2b2433641b95Dd330A33185A44")

    # strategy.setKeeper(keeper, {'from': strategist})

    # carlos = accounts.at("0x73f2f3A4fF97B6A6d7afc03C449f0e9a0c0d90aB", force=True)

    # keeper.addStrategy(strategy, 1700000, 10, {'from': carlos})

    bot = accounts.at("0xfe56a0dbdad44Dd14E4d560632Cc842c8A13642b", force=True)

    assert keeper.harvestable(strategy) == False

    depositAmount = Wei("3500 ether")
    deposit(depositAmount, whale, currency, vault)

    assert keeper.harvestable(strategy) == False

    depositAmount = Wei("1000 ether")
    deposit(depositAmount, whale, currency, vault)
    assert keeper.harvestable(strategy) == True

    keeper.harvest(strategy, {"from": bot})
    balanceBefore = kp3r.balanceOf(bot)
    # print(tx.events)
    chain.mine(4)
    # assert kp3r.balanceOf(bot) > balanceBefore
    # strategy.harvest({'from': strategist})

    assert keeper.harvestable(strategy) == False

    stateOfStrat(strategy, dai, comp)
    genericStateOfVault(vault, dai)

    # stateOfStrat(strategy, dai, comp)
    # stateOfVault(vault, strategy)
    # depositAmount =  Wei('1000 ether')

    # deposit(depositAmount, whale, currency, vault)

    # stateOfStrat(strategy, dai, comp)
    # genericStateOfVault(vault, dai)

    # strategy.harvest({'from': strategist})

    # stateOfStrat(strategy, dai, comp)
    # genericStateOfVault(vault, dai)


def test_wind_down_orb(Contract, web3, accounts, chain):
    daihard = Contract("0xBFa4D8AA6d8a379aBFe7793399D3DdaCC5bBECBB")
    orbStrat = Contract("0x2476eC85e55625Eb658CAFAFe5fdc0FAE2954C85")
    gov = accounts.at(daihard.governance(), force=True)
    daiStrat = Contract(daihard.withdrawalQueue(0))
    daihard.revokeStrategy(daiStrat, {"from": gov})
    dai = Contract(daihard.token())

    daiStrat.harvest({"from": gov})

    orb_vault = Contract(orbStrat.vault())
    weth = Contract(orb_vault.token())
    gov = accounts.at(orb_vault.governance(), force=True)
    orb_vault.revokeStrategy(orbStrat, {"from": gov})

    strategist = accounts.at(orbStrat.strategist(), force=True)
    orbStrat.harvest({"from": strategist})

    print("\n Deposit limit: ", orb_vault)

    print("\nEnd balances Strat")
    print("WETH: ", weth.balanceOf(orbStrat) / 1e18)
    print("yvDAI: ", daihard.balanceOf(orbStrat) / 1e18)
    print("DAI: ", dai.balanceOf(orbStrat) / 1e18)

    print("\nEnd balances Vault")
    print("WETH: ", weth.balanceOf(orb_vault) / 1e18)
    print("yvDAI: ", daihard.balanceOf(orb_vault) / 1e18)
    print("DAI: ", dai.balanceOf(orb_vault) / 1e18)

    genericStateOfStrat(orbStrat, weth, orb_vault)
