import pytest
from brownie import Wei, config
from brownie import network


# change these fixtures for generic tests
@pytest.fixture
def currency(interface):
    # this one is dai:
    #yield interface.ERC20("0x6b175474e89094c44da98b954eedeac495271d0f")
    # this one is weth:
    yield interface.ERC20('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')


@pytest.fixture
def vault(gov, rewards, guardian, currency, pm, Vault):

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
def whale(accounts, web3, weth, dai, usdc, gov, chain):
    network.gas_price("0 gwei")
    network.gas_limit(6700000)
    # big binance7 wallet
    # acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    # big binance8 wallet
    # acc2 = accounts.at("0xf977814e90da44bfa03b6295a0616a897441acec", force=True)

    # polygon bridge
    #acc = accounts.at("0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf", force=True)

    # maker eth bridge
    acc = accounts.at("0x2F0b23f53734252Bda2277357e97e1517d6B042A", force=True)
    
    # usdc.transfer(acc, usdc.balanceOf(acc2), {"from": acc2})
    # lots of weth account
    # if weth transfer fails change to new weth account
    # wethAcc = accounts.at('0x1840c62fD7e2396e470377e6B2a833F3A1E96221', force=True)

    # weth.transfer(acc, weth.balanceOf(wethAcc),{"from": wethAcc} )

    wethDeposit = 100 *1e18
    #daiDeposit = 10000 * 1e18

    # assert weth.balanceOf(acc)  > wethDeposit
    #assert dai.balanceOf(acc) > 1_000_000 * 1e18
    #assert usdc.balanceOf(acc) > 1_000_000 * 1e6

    weth.transfer(gov, wethDeposit,{"from": acc} )
    #dai.transfer(gov, daiDeposit, {"from": acc})

    #  assert  weth.balanceOf(acc) > 0
    yield acc


@pytest.fixture()
def strategist(accounts, whale, currency):
    decimals = currency.decimals()
    currency.transfer(accounts[1], 100 * (10 ** decimals), {"from": whale})
    yield accounts[1]


@pytest.fixture
def samdev(accounts):
    yield accounts.at("0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0", force=True)


@pytest.fixture
def gov(accounts):
    yield accounts[3]


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
def dai(interface):
    yield interface.ERC20("0x6b175474e89094c44da98b954eedeac495271d0f")


@pytest.fixture
def usdc(interface):
    yield interface.ERC20("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")

@pytest.fixture
def live_vault_042(Vault):
    yield Vault.at("0xa258C4606Ca8206D8aA700cE2143D7db854D168c")


@pytest.fixture
def live_strategy_weth_042(Strategy):
    yield Strategy.at("0x83B6211379c26E0bA8d01b9EcD4eE1aE915630aa")

@pytest.fixture
def dai(interface):
    yield interface.ERC20("0x6b175474e89094c44da98b954eedeac495271d0f")


# uniwethwbtc
@pytest.fixture
def uni_wethwbtc(interface):
    yield interface.ERC20("0xBb2b8038a1640196FbE3e38816F3e67Cba72D940")


@pytest.fixture
def samdev(accounts):
    yield accounts.at("0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0", force=True)


@pytest.fixture
def earlyadopter(accounts):
    yield accounts.at("0x769B66253237107650C3C6c84747DFa2B071780e", force=True)


@pytest.fixture
def comp(interface):
    yield interface.ERC20("0xc00e94Cb662C3520282E6f5717214004A7f26888")


@pytest.fixture
def ceth(interface):
    yield interface.CErc20I("0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5")


@pytest.fixture
def cusdc(interface):
    yield interface.CErc20I("0x39AA39c021dfbaE8faC545936693aC917d5E7563")


# @pytest.fixture(autouse=True)
# def isolation(fn_isolation):
#    pass
@pytest.fixture(scope="module", autouse=True)
def shared_setup(module_isolation):
    pass


@pytest.fixture
def gov(accounts):
    yield accounts[0]


@pytest.fixture
def live_gov(accounts):
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)


@pytest.fixture
def rando(accounts):
    yield accounts[9]


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


@pytest.fixture()
def strategy(strategist, gov, keeper, vault, Strategy, ceth,health_check):
    strategy = strategist.deploy(Strategy, vault, ceth)
    strategy.setHealthCheck(health_check, {"from": gov})

    rate_limit = 300_000_000 * 1e18

    debt_ratio = 10_000  # 100%
    vault.addStrategy(strategy, debt_ratio, 0, rate_limit, 1000, {"from": gov})

    yield strategy


@pytest.fixture()
def largerunningstrategy(gov, strategy, weth, vault, whale):

    amount = Wei("500 ether")
    weth.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})

    strategy.harvest({"from": gov})

    # do it again with a smaller amount to replicate being this full for a while
    amount = Wei("10 ether")
    weth.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.harvest({"from": gov})

    yield strategy

@pytest.fixture()
def health_check(Contract):
    yield Contract('0xddcea799ff1699e98edf118e0629a974df7df012')

@pytest.fixture()
def enormousrunningstrategy(gov, largerunningstrategy, weth, vault, whale, chain):
    deposit_amount = 1_000 * 1e18
    weth.approve(vault, weth.balanceOf(whale), {"from": whale})
    vault.deposit(deposit_amount, {"from": whale})
    

    collat = 0

    while collat < largerunningstrategy.collateralTarget() / 1.001e18:

        tx = largerunningstrategy.harvest({"from": gov})
        chain.sleep(1)
        chain.mine(1)
        
        deposits, borrows = largerunningstrategy.getCurrentPosition()
        collat = borrows / deposits
        print(collat)

    yield largerunningstrategy
