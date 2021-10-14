import brownie
from brownie import interface, chain, Contract


def vault_status(vault):
    print(f"--- Vault {vault.name()} ---")
    print(f"API: {vault.apiVersion()}")
    print(f"TotalAssets: {to_units(vault, vault.totalAssets())}")
    print(f"PricePerShare: {to_units(vault, vault.pricePerShare())}")
    print(f"TotalSupply: {to_units(vault, vault.totalSupply())}")


def strategy_status(vault, strategy):
    status = vault.strategies(strategy).dict()
    print(f"--- Strategy {strategy.name()} ---")
    print(f"Performance fee {status['performanceFee']}")
    print(f"Debt Ratio {status['debtRatio']}")
    print(f"Total Debt {to_units(vault, status['totalDebt'])}")
    print(f"Total Gain {to_units(vault, status['totalGain'])}")
    print(f"Total Loss {to_units(vault, status['totalLoss'])}")
    
    supply, borrows = strategy.getCurrentPosition()
    token = Contract(strategy.want())
    print(f"Want: {to_units(vault, token.balanceOf(strategy)):,.2f}")
    print(f"Supply: {to_units(vault, supply):,.2f}")
    print(f"Borrow: {to_units(vault, borrows):,.2f}")
    print(f"Collateral Ratio: {(strategy.storedCollateralisation()/1e18)*100:,.4f}%")
    print(f"Target Ratio: {(strategy.collateralTarget()/1e18)*100:,.4f}%")



def to_units(token, amount):
    return amount / (10 ** token.decimals())


def from_units(token, amount):
    return amount * (10 ** token.decimals())


# default: 8 hours (sandwich protection)
def sleep(seconds=8 * 60 * 60):
    chain.sleep(seconds)
    chain.mine(1)
