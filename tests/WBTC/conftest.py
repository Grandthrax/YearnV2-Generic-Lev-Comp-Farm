import pytest
from brownie import Wei, config, chain
from brownie import network, Contract

@pytest.fixture(scope="function", autouse=True)
def isolation(fn_isolation):
    pass

@pytest.fixture(autouse=True)
def FlashLoanLibrary(FlashLoanLib, gov):
    yield gov.deploy(FlashLoanLib)

@pytest.fixture
def currency(wbtc):
    yield wbtc

@pytest.fixture(scope="function")
def vault(gov, rewards, guardian, currency, pm, Vault, isolation):
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian, gov, {"from": gov})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})

    yield vault

@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract

@pytest.fixture
def Vault(pm):
    yield pm(config["dependencies"][0]).Vault

@pytest.fixture
def weth(interface):
    yield interface.ERC20("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

@pytest.fixture
def whale(accounts):
    yield accounts.at("0x9ff58f4ffb29fa2266ab25e75e2a8b3503311656", force=True)

@pytest.fixture
def factory(LevCompFactory, strategist, vault, cToken):
    factory = strategist.deploy(LevCompFactory, vault, cToken)
    yield factory

@pytest.fixture()
def strategist(accounts, whale, currency):
    decimals = currency.decimals()
    currency.transfer(accounts[1], 100 * (10 ** decimals), {"from": whale})
    yield accounts[1]

@pytest.fixture(autouse=True)
def refill_comptroller(comp):
    comptroller = Contract("0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B")
    reservoir = Contract("0x2775b1c75658Be0F640272CCb8c72ac986009e38")
    comp.transfer(comptroller, comp.balanceOf(reservoir), {'from': reservoir})

@pytest.fixture
def gov(accounts):
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)

@pytest.fixture
def user(accounts, whale, currency):
    currency.transfer(accounts[0], 4000e8, {'from': whale})
    yield accounts[0]

@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]
    
@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]


@pytest.fixture
def rando(accounts):
    yield accounts[9]

@pytest.fixture
def wbtc(interface):
    yield interface.ERC20("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")

@pytest.fixture
def cToken(interface):
    yield interface.CErc20I("0xccF4429DB6322D5C611ee964527D42E5d685DD6a")

# uniwethwbtc
@pytest.fixture
def uni_wethwbtc(interface):
    yield interface.ERC20("0xBb2b8038a1640196FbE3e38816F3e67Cba72D940")

@pytest.fixture
def comp(interface):
    yield interface.ERC20("0xc00e94Cb662C3520282E6f5717214004A7f26888")

@pytest.fixture
def cwbtc(interface):
    yield interface.CErc20I("0xccF4429DB6322D5C611ee964527D42E5d685DD6a")

@pytest.fixture
def strategy(strategist, gov, keeper, vault, Strategy, cToken, health_check, weth):
    strategy = strategist.deploy(Strategy, vault, cToken)
    strategy.setHealthCheck(health_check, {"from": gov})

    rate_limit = 300_000_000 * 1e18

    debt_ratio = 10_000  # 100%
    vault.addStrategy(strategy, debt_ratio, 0, rate_limit, 1000, {"from": gov})

    # send WETH to repay 2 wei+ each flashloan
    weth.transfer(strategy, 1e6, {'from': '0xBA12222222228d8Ba445958a75a0704d566BF2C8'})
    chain.sleep(1)
    chain.mine()
    yield strategy

@pytest.fixture
def big_strategy(vault, strategy, gov, currency, user, whale):
    currency.approve(vault, 2 ** 256 - 1, {'from': user})
    currency.transfer(user, 1000 * 1e8, {'from': whale})
    vault.deposit({'from': user})
    chain.sleep(1)
    chain.mine()
    strategy.harvest({'from': gov})

    yield strategy

@pytest.fixture()
def health_check(Contract):
    yield Contract('0xddcea799ff1699e98edf118e0629a974df7df012')
