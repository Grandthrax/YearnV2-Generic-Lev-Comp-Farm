pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "./Interfaces/DyDx/ISoloMargin.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/math/Math.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "./Interfaces/Compound/CErc20I.sol";
import "./Interfaces/Compound/CEtherI.sol";
import "./Interfaces/Compound/ComptrollerI.sol";
import "./Interfaces/DyDx/ISoloMargin.sol";

interface IUniswapAnchoredView {
    function price(string memory) external returns (uint);
}

interface IWETH is IERC20 {
    function deposit() payable external;
    function withdraw(uint256) external;
}

contract WBTCFlashLoan {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    ISoloMargin private constant solo = ISoloMargin(0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e);

    ComptrollerI private constant compound = ComptrollerI(0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B);
    address private constant comp = 0xc00e94Cb662C3520282E6f5717214004A7f26888;
    IERC20 public wbtc = IERC20(0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599);
    IWETH public weth = IWETH(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    CErc20I public cToken = CErc20I(0xccF4429DB6322D5C611ee964527D42E5d685DD6a);
    CEtherI public cEth = CEtherI(0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5);
    IUniswapAnchoredView public oracle = IUniswapAnchoredView(0x841616a5CBA946CF415Efe8a326A621A794D0f97);
    uint constant public PRICE_DECIMALS = 10 ** 6;

    uint256 constant public collateralRatioETH = 0.75 ether; // 75%
    uint marketId = 0; // ETH

    event Number(string name, uint number);

    // needs to be able to receive ETH
    receive() external payable {

    }

    function takeWBTCFlashLoan() public {
        uint256 desiredWBTC = 1e8; // 1 WBTC
        // calculate how much ETH we need to get WBTC
        // price ETH / BTC
        uint ETHBTC = oracle.price("ETH").mul(PRICE_DECIMALS).div(oracle.price("BTC"));
        // ETH = desiredWBTCinETH / collatRatioETH (remember to adjust decimals 8 => 18)
        uint256 amountRequiredETH = 
            desiredWBTC.mul(PRICE_DECIMALS).mul(1e10)
                .mul(1e18).div(collateralRatioETH)
                .div(ETHBTC);

        emit Number("ETHUSD", oracle.price("ETH"));
        emit Number("BTCUSD", oracle.price("BTC"));
        emit Number("ETHBTC", ETHBTC);
        emit Number("amountRequiredETH", amountRequiredETH);

        amountRequiredETH = amountRequiredETH.mul(105).div(100); // 5% more just in case
        emit Number("amountRequiredETH", amountRequiredETH);

        // uint256 dydxLiquidity = _getDyDxLiquidity();
        uint256 dydxLiquidity = 1000 ether;

        // adjust for liquidity 
        amountRequiredETH = Math.min(amountRequiredETH, dydxLiquidity);

        Actions.ActionArgs[] memory actions = new Actions.ActionArgs[](3);

        // take ETH flash loan
        actions[0] = _getWithdrawAction(amountRequiredETH);

        // CALL OPERATE
            // supply ETH to Compound
            // borrow desired WBTC from Compound
            // do stuff with WBTC
            // repay desired WBTC to Compound
            // withdraw ETH from Compound
        actions[1] = _getCallAction(desiredWBTC);

        // repay ETH flash loan
        actions[2] = _getDepositAction(amountRequiredETH.add(2));

        Account.Info[] memory accounts = new Account.Info[](1);
        accounts[0] = Account.Info({
            owner: address(this),
            number: 1 // why 1?
        });

        // execute
        solo.operate(accounts, actions);

        // return to initial balance
        require(wbtc.balanceOf(address(this)) == 0);
        require(address(this).balance == 0);
    }

    function callFunction(
        address sender,
        Account.Info memory accountInfo,
        bytes memory data
    ) external {
        require(sender == address(this));
        uint amount = abi.decode(data, (uint));

        // supply ETH to compound
        // NOTE: we supply full balance
        uint wethBalance = weth.balanceOf(address(this));
        emit Number("availableETH", payable(address(this)).balance);
        emit Number("wethBalance", wethBalance);
        weth.withdraw(wethBalance);
        emit Number("availableETH", payable(address(this)).balance);
        uint availableETH = payable(address(this)).balance;
        {
            address[] memory markets = new address[](1);
            markets[0] = address(cEth);
            compound.enterMarkets(markets);

        }
        cEth.mint{value: availableETH}(); // will revert if it fails
        emit Number("amount", amount);

        // borrow WBTC from Compound
        require(cToken.borrow(amount) == 0, "!borrow");

        // do stuff with WBTC
        require(wbtc.balanceOf(address(this)) == amount, "!no-btc");

        // repay WBTC
        wbtc.safeApprove(address(cToken), 0); // due to safeApprove
        wbtc.safeApprove(address(cToken), type(uint256).max);

        require(cToken.repayBorrow(amount) == 0, "!repay");

        // withdraw ETH from Compound
        require(cEth.redeemUnderlying(availableETH) == 0, "!redeem");
        emit Number("availableETH", payable(address(this)).balance);

        weth.deposit{value: payable(address(this)).balance}();
        emit Number("balanceWETH", weth.balanceOf(address(this)));
        emit Number("balanceCeth", cEth.balanceOf(address(this)));

        IERC20(address(weth)).safeApprove(address(solo), 0); // due to safeApprove
        IERC20(address(weth)).safeApprove(address(solo), type(uint256).max);
    }

    // INTERNAL
    function _getWithdrawAction(uint amount) internal returns (Actions.ActionArgs memory) {
        return Actions.ActionArgs({
            actionType: Actions.ActionType.Withdraw,
            accountId: 0,
            amount: Types.AssetAmount({
                sign: false,
                denomination: Types.AssetDenomination.Wei,
                ref: Types.AssetReference.Delta,
                value: amount
            }),
            primaryMarketId: marketId,
            secondaryMarketId: 0,
            otherAddress: address(this),
            otherAccountId: 0,
            data: ""
        });
    }

    function _getCallAction(uint amount) internal returns (Actions.ActionArgs memory) {
        // generate Data
        bytes memory _data = abi.encode(amount);

        return Actions.ActionArgs({
            actionType: Actions.ActionType.Call,
            accountId: 0,
            amount: Types.AssetAmount({
                sign: false, 
                denomination: Types.AssetDenomination.Wei,
                ref: Types.AssetReference.Target,
                value: 0
            }),
            primaryMarketId: 0,
            secondaryMarketId: 0,
            otherAddress: address(this),
            otherAccountId: 0,
            data: _data
        });
    }

    function _getDepositAction(uint amount) internal returns (Actions.ActionArgs memory) {
        return Actions.ActionArgs({
            actionType: Actions.ActionType.Deposit,
            accountId: 0,
            amount: Types.AssetAmount({
                sign: true, 
                denomination: Types.AssetDenomination.Wei,
                ref: Types.AssetReference.Target,
                value: 0
           }),
            primaryMarketId: marketId,
            secondaryMarketId: 0,
            otherAddress: address(this),
            otherAccountId: 0,
            data: ""
        });
    }
}