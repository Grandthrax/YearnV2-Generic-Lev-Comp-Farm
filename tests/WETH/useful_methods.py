from itertools import count
from brownie import Wei, reverts, network
import brownie
import requests


def get_gas_price(confirmation_speed: str = "fast"):
    if "mainnet" not in network.show_active():
        return 10 ** 9  # 1 gwei
    data = requests.get("https://www.gasnow.org/api/v3/gas/price").json()
    return data["data"][confirmation_speed]


# note you can use real gas prices and estimates here but for testing better to hardcode
def harvest(strategy, keeper, vault):
    # Evaluate gas cost of calling harvest
    # gasprice = get_gas_price()
    gasprice = 30 * 1e9
    # txgas = strategy.harvest.estimate_gas()
    txgas = 1500000  # 1.5m
    txGasCost = txgas * gasprice
    avCredit = vault.creditAvailable(strategy)
    if avCredit > 0:
        print("Available credit from vault: ", avCredit / 1e18)
    harvestCondition = strategy.harvestTrigger(txGasCost, {"from": keeper})
    if harvestCondition:
        print("\n----bot calls harvest----")
        print("Tx harvest() gas cost: ", txGasCost / 1e18)
        print("Gas price: ", gasprice / 1e9)
        tx = strategy.harvest({"from": keeper})
        print(tx.events['StrategyReported'])


def tend(strategy, keeper):

    tendCondition = strategy.tendTrigger(0, {"from": keeper})

    if tendCondition:
        print("\n----bot calls tend----")
        strategy.tend({"from": keeper})


def stateOfStrat(strategy, dai, comp):
    print("\n----state of strat----")

    decimals = dai.decimals()
    deposits, borrows = strategy.getCurrentPosition()
    compBal = comp.balanceOf(strategy)
    print("Comp:", compBal/1e18)
    print("Want:", "{:,.1f}".format(dai.balanceOf(strategy) / (10 ** decimals)))
    print("borrows:", borrows / (10 ** decimals))
    print("deposits:", "{:,.1f}".format(deposits / (10 ** decimals)))
    realbalance = dai.balanceOf(strategy) + deposits - borrows
    print("total assets real:", "{:,.1f}".format(realbalance / (10 ** decimals)))

    print(
        "total assets estimate:",
        "{:,.1f}".format(strategy.estimatedTotalAssets() / (10 ** decimals)),
    )
    if deposits == 0:
        collat = 0
    else:
        collat = borrows / deposits
    leverage = 1 / (1 - collat)
    print(f"calculated collat: {collat:.5%}")
    storedCollat = strategy.storedCollateralisation() / 1e18
    print(f"stored collat: {storedCollat:.5%}")
    print(f"leverage: {leverage:.5f}x")
    assert collat <= 0.75
    print("Expected Profit:", strategy.expectedReturn() / (10 ** decimals))
    toLiquidation = strategy.getblocksUntilLiquidation()
    print("Weeks to liquidation:", toLiquidation / 44100)


def genericStateOfStrat(strategy, currency, vault):
    decimals = currency.decimals()
    print(f"\n----state of {strategy.name()}----")

    print("Want:", currency.balanceOf(strategy) / (10 ** decimals))
    print("Total assets estimate:", strategy.estimatedTotalAssets() / (10 ** decimals))
    strState = vault.strategies(strategy)
    totalDebt = strState.dict()['totalDebt'] / (10 ** decimals)
    debtLimit = strState.dict()['debtRatio'] 
    totalLosses = strState.dict()['totalLoss'] / (10 ** decimals)
    totalReturns = strState.dict()['totalGain'] / (10 ** decimals)
    print(f"Total Strategy Debt: {totalDebt:.5f}")
    print(f"Strategy Debt Limit: {debtLimit:.5f}")
    print(f"Total Strategy Gains: {totalReturns}")
    print(f"Total Strategy losses: {totalLosses}")
    print("Harvest Trigger:", strategy.harvestTrigger(1000000 * 30 * 1e9))
    print(
        "Tend Trigger:", strategy.tendTrigger(1000000 * 30 * 1e9)
    )  # 1m gas at 30 gwei
    print("Emergency Exit:", strategy.emergencyExit())


def genericStateOfVault(vault, currency):
    decimals = currency.decimals()
    print(f"\n----state of {vault.name()} vault----")
    balance = vault.totalAssets() / (10 ** decimals)
    print(f"Total Assets: {balance:.5f}")
    balance = vault.totalDebt() / (10 ** decimals)
    pricePerShare = vault.pricePerShare() / (10 ** decimals)
    print("Loose balance in vault:", currency.balanceOf(vault) / (10 ** decimals))
    print(f"Total Debt: {balance:.5f}")
    print(f"Price Per Share: {pricePerShare:.5f}")


def assertCollateralRatio(strategy):
    deposits, borrows = strategy.getCurrentPosition()
    collat = borrows / deposits
    assert collat <= strategy.collateralTarget() / 1e18


def stateOfVault(vault, strategy):
    print("\n----state of vault----")
    strState = vault.strategies(strategy)
    totalDebt = strState.dict()['totalDebt']
    totalReturns = strState.dict()['totalGain']
    print(f"Total Strategy Debt: {totalDebt:.5f}")
    print(f"Total Strategy Returns: {totalReturns:.5f}")
    balance = vault.totalAssets().to("ether")
    print(f"Total Assets: {balance:.5f}")


def wait(blocks, chain):
    print(f"\nWaiting {blocks} blocks")
    timeN = chain.time()
    endTime = blocks * 13 + timeN
    chain.mine(blocks, endTime)


def sleep(chain, blocks):
    timeN = chain.time()
    endTime = blocks * 13 + timeN
    chain.mine(blocks, endTime)


def deposit(amount, user, dai, vault):
    print("\n----user deposits----")
    dai.approve(vault, amount, {"from": user})
    print("deposit amount:", amount.to("ether"))
    vault.deposit(amount, {"from": user})


def withdraw(share, whale, dai, vault):
    balanceBefore = dai.balanceOf(whale)
    balance = vault.balanceOf(whale)

    withdraw = min(balance, balance / share)
    wits = withdraw / 1e18

    print(f"\n----user withdraws {wits}----")
    vault.withdraw(withdraw, {"from": whale})
    balanceAfter = dai.balanceOf(whale)
    moneyOut = balanceAfter - balanceBefore
    print("Money Out:", Wei(moneyOut).to("ether"))
