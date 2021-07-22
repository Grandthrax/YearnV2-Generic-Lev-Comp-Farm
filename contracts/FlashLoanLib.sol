pragma solidity 0.6.12; 
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "./Interfaces/DyDx/DydxFlashLoanBase.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./Interfaces/Compound/CEtherI.sol";
import "./Interfaces/Compound/CErc20I.sol";
import "./Interfaces/Compound/ComptrollerI.sol";

interface IWETH is IERC20 {
    function deposit() payable external;
    function withdraw(uint256) external;
}

interface IUniswapAnchoredView {
    function price(string memory) external returns (uint);
}

library FlashLoanLib {
    using SafeMath for uint256;
    event Leverage(uint256 amountRequested, uint256 amountGiven, bool deficit, address flashLoan);
    address private constant SOLO = 0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e;
    uint256 constant private PRICE_DECIMALS = 10 ** 6;
    uint256 constant private collatRatioETH = 0.75 ether;
    IUniswapAnchoredView constant private oracle = IUniswapAnchoredView(0x841616a5CBA946CF415Efe8a326A621A794D0f97);
    address private constant weth = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    CEtherI public constant cEth = CEtherI(0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5);
    ComptrollerI private constant compound = ComptrollerI(0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B);

    function doDyDxFlashLoan(bool deficit, uint256 amountDesired, CErc20I cToken) public returns (uint256) {
        if(amountDesired == 0){
            return 0;
        }
        uint256 amountWBTC = amountDesired;
        ISoloMargin solo = ISoloMargin(SOLO);

        // calculate amount of ETH we need
        uint256 requiredETH; 
        {
            // TODO: add oracle to state variables
            uint256 priceETHBTC = oracle.price("ETH").mul(PRICE_DECIMALS).div(oracle.price("BTC"));
            // requiredETH = desiredWBTCInETH / collatRatioETH
            // desiredWBTCInETH = (desiredWBTC / priceETHBTC)
            // NOTE: decimals need adjustment (BTC: 8 + ETH: 18)
            requiredETH = amountWBTC.mul(PRICE_DECIMALS).mul(1e18).mul(1e10).div(priceETHBTC).div(collatRatioETH);
            // requiredETH = requiredETH.mul(101).div(100); // +1% just in case (TODO: not needed?)
                    // Not enough want in DyDx. So we take all we can

            uint256 dxdyLiquidity = IERC20(weth).balanceOf(address(solo));
            if(requiredETH > dxdyLiquidity) {
                requiredETH = dxdyLiquidity;
                // NOTE: if we cap amountETH, we reduce amountWBTC we are taking too
                amountWBTC = requiredETH.mul(collatRatioETH).div(priceETHBTC).div(1e18).div(1e10);
            }
        }

        // Array of actions to be done during FlashLoan
        Actions.ActionArgs[] memory operations = new Actions.ActionArgs[](3);

        // 1. Take FlashLoan
        operations[0] = _getWithdrawAction(0, requiredETH); // hardcoded market ID to 0 (ETH)

        // 2. Encode arguments of functions and create action for calling it 
        bytes memory data = abi.encode(deficit, amountWBTC);
        // This call will: 
        // Unwrap WETH to ETH
        // supply ETH to Compound
        // borrow desired WBTC from Compound
        // do stuff with WBTC
        // repay desired WBTC to Compound
        // withdraw ETH from Compound
        operations[1] = _getCallAction(
            data
        );

        // 3. Repay FlashLoan
        operations[2] = _getDepositAction(0, requiredETH.add(2));

        // Create Account Info
        Account.Info[] memory accountInfos = new Account.Info[](1);
        accountInfos[0] = _getAccountInfo();

        solo.operate(accountInfos, operations);

        emit Leverage(amountDesired, requiredETH, deficit, address(solo));

        return amountWBTC; // we need to return the amount of WBTC we have changed our position in
    }


    function loanLogic(
        bool deficit,
        uint256 amount,
        CErc20I cToken
    ) public {
        uint256 bal = IERC20(weth).balanceOf(address(this));
        // TODO: does it make sense to check against amount? safer than checking > 0 
        // NOTE: weth balance should always be > amount/0.75
        require(bal >= amount, "!bal"); // to stop malicious calls
        // TODO: add weth to state variables

        uint256 wethBalance = IERC20(weth).balanceOf(address(this));
        IWETH(weth).withdraw(wethBalance);
        // will revert if it fails
        // 1. Deposit ETH in Compound as collateral
        cEth.mint{value: wethBalance}();
        // 2. Borrow want from Compound (just enough to avoid liquidations)
        require(cToken.borrow(amount) == 0, "!borrow0");
        // 3. Use borrowed want
        //if in deficit we repay amount and then withdraw
        if (deficit) {
            require(cToken.repayBorrow(amount) == 0, "!repay1");
            //if we are withdrawing we take more to cover fee
            require(cToken.redeemUnderlying(amount) == 0, "!redeem1");
        } else {
            //check if this failed incase we borrow into liquidation
            require(cToken.mint(IERC20(cToken.underlying()).balanceOf(address(this))) == 0, "!mint");
            //borrow more to cover fee
            // fee is so low for dydx that it does not effect our liquidation risk.
            //DONT USE FOR AAVE
            require(cToken.borrow(amount) == 0, "!borrow1");
        }
        // 4. Repay want
        require(cToken.repayBorrow(amount) == 0, "!repay");
        // 5. Redeem collateral (ETH borrowed from DyDx) from Compound
        // NOTE: we take 2 wei more to repay DyDx flash loan
        // we airdrop WETH to replace this (for gas savings)
        // require(cEth.borrow(2) == 0, "!borrow2");
        require(cEth.redeemUnderlying(wethBalance) == 0, "!redeem");
        // 6. Wrap ETH into WETH
        IWETH(weth).deposit{value: address(this).balance}();

        // NOTE: after this, WETH will be taken by DyDx
    }

    function _getAccountInfo() internal view returns (Account.Info memory) {
        return Account.Info({owner: address(this), number: 1});
    }

    function _getWithdrawAction(uint256 marketId, uint256 amount) internal view returns (Actions.ActionArgs memory) {
        return
            Actions.ActionArgs({
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

    function _getCallAction(bytes memory data) internal view returns (Actions.ActionArgs memory) {
        return
            Actions.ActionArgs({
                actionType: Actions.ActionType.Call,
                accountId: 0,
                amount: Types.AssetAmount({sign: false, denomination: Types.AssetDenomination.Wei, ref: Types.AssetReference.Delta, value: 0}),
                primaryMarketId: 0,
                secondaryMarketId: 0,
                otherAddress: address(this),
                otherAccountId: 0,
                data: data
            });
    }

    function _getDepositAction(uint256 marketId, uint256 amount) internal view returns (Actions.ActionArgs memory) {
        return
            Actions.ActionArgs({
                actionType: Actions.ActionType.Deposit,
                accountId: 0,
                amount: Types.AssetAmount({
                    sign: true,
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
}