from itertools import count
from brownie import Wei, reverts
from useful_methods import (
    stateOfStrat,
    genericStateOfStrat,
    stateOfVault,
    deposit,
    wait,
    withdraw,
    harvest,
    assertCollateralRatio,
)
import brownie


# usdc should revert because of reentry revert
def test_usdc_liq(
    web3, chain, interface, largerunningstrategy_usdc, whale, gov, comp
):
    strategy =largerunningstrategy_usdc

    ctoken = interface.CErc20I(strategy.cToken())
    currency = interface.ERC20(strategy.want())
    decimals = currency.decimals()

    #lets remove liquidity to take us to the wire
    deposits, borrows = strategy.getCurrentPosition()
    theolent = borrows/0.75
    space = deposits - theolent

    # need to do less because of accrued interest and rounding error
    strategy.manualReleaseWant(space-(0.1 * (10**decimals)), {'from': gov}) 
    chain.mine(20)
    ctoken.mint(0, {'from': gov})
    assert strategy.storedCollateralisation() > 0.75*1e18

    currency.approve(ctoken, 2**256-1, {"from": whale})
    with brownie.reverts("re-entered"):
        ctoken.liquidateBorrow(strategy, 100_000 * (10**decimals), ctoken, {'from': whale})


def test_dai_liq(
    web3, chain, interface, largerunningstrategy, whale, gov, comp
):
    strategy =largerunningstrategy

    ctoken = interface.CErc20I(strategy.cToken())
    currency = interface.ERC20(strategy.want())
    decimals = currency.decimals()

    #lets remove liquidity to take us to the wire
    deposits, borrows = strategy.getCurrentPosition()
    theolent = borrows/0.75
    space = deposits - theolent

    # need to do less because of accrued interest and rounding error
    strategy.manualReleaseWant(space-(0.1 * (10**decimals)), {'from': gov}) 
    chain.mine(20)
    ctoken.mint(0, {'from': gov})
    assert strategy.storedCollateralisation() > 0.75*1e18

    currency.approve(ctoken, 2**256-1, {"from": whale})
    ctoken.liquidateBorrow(strategy, 100_000 * (10**decimals), ctoken, {'from': whale})
    assert strategy.storedCollateralisation() < 0.75*1e18