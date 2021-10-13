from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, withdraw, stateOfStrat,genericStateOfVault, deposit, tend, sleep, harvest
import random
import brownie

def test_full_generic(Strategy, web3, chain, cdai, Vault,currency, weth, whale, strategist):
    #our humble strategist is going to publish both the vault and the strategy

    #deploy vault
    vault = strategist.deploy(Vault)
    vault.initialize(currency, strategist, strategist, "", "", strategist)
   
    deposit_limit = Wei('1_000_000 ether')

    #set limit to the vault
    vault.setDepositLimit(deposit_limit, {"from": strategist})

    #deploy strategy
    strategy = strategist.deploy(Strategy, vault, cdai)
    weth.transfer(strategy, 1e6, {'from': '0xBA12222222228d8Ba445958a75a0704d566BF2C8'})
    chain.sleep(1)
    strategy.setMinCompToSell(0.01*1e18, {"from": strategist})

    rate_limit = 1_000_000_000 *1e18
    
    debt_ratio = 9_500 #100%
    vault.addStrategy(strategy, debt_ratio,0, rate_limit, 1000, {"from": strategist})


    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    
    #our humble strategist deposits some test funds
    depositAmount =  Wei('501 ether')
    currency.transfer(strategist, depositAmount, {"from": whale})
    starting_balance = currency.balanceOf(strategist)
    
    deposit(depositAmount, strategist, currency, vault)
    #print(vault.creditAvailable(strategy))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    assert strategy.estimatedTotalAssets() == 0
    assert strategy.harvestTrigger(1e15) == True
    strategy.harvest({"from": strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    assert strategy.estimatedTotalAssets() >= depositAmount*0.999999*(debt_ratio/10_000) #losing some dust is ok

    #whale deposits as well
    whale_deposit  = Wei('2000 ether')
    deposit(whale_deposit, whale, currency, vault)
    harvest(strategy, strategist, vault)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    for i in range(5):
        waitBlock = random.randint(10,50)
        print(f'\n----wait {waitBlock} blocks----')
        sleep(chain, waitBlock)

        #if harvest condition harvest. if tend tend
        harvest(strategy, strategist, vault)
        tend(strategy, strategist)
        something= True
        action = random.randint(0,9)
        if action == 1:
            withdraw(random.randint(50,100),whale, currency, vault)
        elif action == 2:
            withdraw(random.randint(50,100),whale, currency, vault)
        elif action == 3:
            deposit(Wei(str(f'{random.randint(10000,50000)} ether')), whale, currency, vault)
        else :
            something = False

        if something:
            genericStateOfStrat(strategy, currency, vault)
            genericStateOfVault(vault, currency)

    #strategist withdraws
    vault.withdraw({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    profit = currency.balanceOf(strategist) - starting_balance

    print(Wei(profit).to('ether'), ' profit')
    print(vault.strategies(strategy)[6].to('ether'), ' total returns of strat')