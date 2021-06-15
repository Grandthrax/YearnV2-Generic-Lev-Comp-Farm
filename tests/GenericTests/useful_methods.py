from brownie import Wei, reverts
import requests
from brownie.network.state import Chain


def genericStateOfStrat(strategy, currency, vault):
    decimals = currency.decimals()
    print(f"\n----state of {strategy.name()}----")

    print("Want:", currency.balanceOf(strategy) / (1 ** decimals))
    print("Total assets estimate:", strategy.estimatedTotalAssets() / (10 ** decimals))
    strState = vault.strategies(strategy)
    totalDebt = strState[5] / (10 ** decimals)
    debtLimit = strState[2] / (10 ** decimals)
    totalLosses = strState[7] / (10 ** decimals)
    totalReturns = strState[6] / (10 ** decimals)
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
    print("Loose balance in vault:", currency.balanceOf(vault) / (10 ** decimals))
    print(f"Total Debt: {balance:.5f}")


def deposit(amount, user, dai, vault):
    # print('\n----user deposits----')
    dai.approve(vault, amount, {"from": user})
    # print('deposit amount:', amount.to('ether'))
    vault.deposit(amount, {"from": user})


def sleep(chain, blocks):
    timeN = chain.time()
    endTime = blocks * 13 + timeN
    chain.mine(blocks, endTime)


def stateOfStrat(strategy, interface):
    print("\n----state of strat----")
    dai = interface.ERC20(strategy.want())
    deposits, borrows = strategy.getCurrentPosition()
    # compBal = comp.balanceOf(strategy)
    # print('Comp:', Wei(compBal).to('ether'))
    print("DAI:", dai.balanceOf(strategy).to("ether"))
    print("borrows:", borrows / 1e18)
    print("deposits:", deposits / 1e18)
    realbalance = dai.balanceOf(strategy) + deposits - borrows
    print("total assets real:", realbalance.to("ether"))

    print("total assets estimate:", strategy.estimatedTotalAssets().to("ether"))
    if deposits == 0:
        collat = 0
    else:
        collat = borrows / deposits
    leverage = 1 / (1 - collat)
    print(f"calculated collat: {collat:.5%}")
    storedCollat = strategy.storedCollateralisation().to("ether")
    print(f"stored collat: {storedCollat:.5%}")
    print(f"leverage: {leverage:.5f}x")
    assert collat <= 0.75
    print("Expected Profit:", strategy.expectedReturn().to("ether"))
    toLiquidation = strategy.getblocksUntilLiquidation()
    print("Weeks to liquidation:", toLiquidation / 44100)
