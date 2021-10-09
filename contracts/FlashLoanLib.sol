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

interface IERC20Extended is IERC20 {
	function decimals() external view returns (uint8);

	function name() external view returns (string memory);

	function symbol() external view returns (string memory);
}

library FlashLoanLib {
	using SafeMath for uint256;
	event Leverage(uint256 amountRequested, uint256 amountGiven, bool deficit, address flashLoan);

	uint256 constant private PRICE_DECIMALS = 1e6;
	uint256 constant private WETH_DECIMALS = 1e18;
	uint256 constant private COLLAT_RATIO_ETH = 0.74 ether;
	address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
	address private constant WBTC = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599;
	ComptrollerI private constant COMP = ComptrollerI(0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B);
	ISoloMargin public constant SOLO = ISoloMargin(0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e);
	CEtherI public constant CETH = CEtherI(0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5);

	function doDyDxFlashLoan(bool deficit, uint256 amountDesired, address want) public returns (uint256) {
		if(amountDesired == 0){
			return 0;
		}
		// calculate amount of ETH we need
		(uint256 requiredETH, uint256 amountWant)= getFlashLoanParams(want, amountDesired); 

		// Array of actions to be done during FlashLoan
		Actions.ActionArgs[] memory operations = new Actions.ActionArgs[](3);

		// 1. Take FlashLoan
		operations[0] = _getWithdrawAction(0, requiredETH); // hardcoded market ID to 0 (ETH)

		// 2. Encode arguments of functions and create action for calling it 
		bytes memory data = abi.encode(deficit, amountWant);

		operations[1] = _getCallAction(
			data
		);

		// 3. Repay FlashLoan
		operations[2] = _getDepositAction(0, requiredETH.add(2));

		// Create Account Info
		Account.Info[] memory accountInfos = new Account.Info[](1);
		accountInfos[0] = _getAccountInfo();

		SOLO.operate(accountInfos, operations);

		emit Leverage(amountDesired, requiredETH, deficit, address(SOLO));

		return amountWant; // we need to return the amount of Want we have changed our position in
	}
	
	function getFlashLoanParams(address want, uint256 amountDesired) internal returns (uint256 requiredETH, uint256 amountWant) {
		(uint256 priceETHWant, uint256 decimalsDifference, uint256 _requiredETH) = getPriceETHWant(want, amountDesired);
		// to avoid stack too deep	
		requiredETH = _requiredETH;
		amountWant = amountDesired;
		// Not enough want in DyDx. So we take all we can
		uint256 dxdyLiquidity = IERC20(WETH).balanceOf(address(SOLO));
		if(requiredETH > dxdyLiquidity) {
			requiredETH = dxdyLiquidity;
			// NOTE: if we cap amountETH, we reduce amountWant we are taking too
			amountWant = requiredETH.mul(COLLAT_RATIO_ETH).div(priceETHWant).div(1e18).div(decimalsDifference);
		}
	}

	function getPriceETHWant(address want, uint256 amountDesired) internal returns (uint256 priceETHWant, uint256 decimalsDifference, uint256 requiredETH) {
		uint256 wantDecimals = 10 ** uint256(IERC20Extended(want).decimals());
		decimalsDifference = WETH_DECIMALS > wantDecimals ? WETH_DECIMALS.div(wantDecimals) : wantDecimals.div(WETH_DECIMALS);
		if(want == WETH) {
			requiredETH = amountDesired.mul(1e18).div(COLLAT_RATIO_ETH);
			priceETHWant = 1e6; // 1:1
		} else {
			priceETHWant = getOraclePrice(WETH).mul(PRICE_DECIMALS).div(getOraclePrice(want));
			// requiredETH = desiredWantInETH / COLLAT_RATIO_ETH
			// desiredWBTCInETH = (desiredWant / priceETHWant)
			// NOTE: decimals need adjustment (e.g. BTC: 8 / ETH: 18)
			requiredETH = amountDesired.mul(PRICE_DECIMALS).mul(1e18).mul(decimalsDifference).div(priceETHWant).div(COLLAT_RATIO_ETH);
		}
	}

	function getOraclePrice(address token) internal returns (uint256) {
		string memory symbol = IERC20Extended(token).symbol(); 
		// Symbol for WBTC is BTC in oracle
		if(token == WBTC) {
			symbol = "BTC";
		} else if (token == WETH) {
			symbol = "ETH";
		}
		IUniswapAnchoredView oracle = IUniswapAnchoredView(COMP.oracle());
		return oracle.price(symbol);
	}

	function loanLogic(
		bool deficit,
		uint256 amount,
		CErc20I cToken
	) public {
		uint256 wethBal = IERC20(WETH).balanceOf(address(this));
		// NOTE: weth balance should always be > amount/0.75
		require(wethBal >= amount, "!bal"); // to stop malicious calls

		uint256 wethBalance = IERC20(WETH).balanceOf(address(this));
		// 0. Unwrap WETH
		IWETH(WETH).withdraw(wethBalance);
		// 1. Deposit ETH in Compound as collateral
		// will revert if it fails
		CETH.mint{value: wethBalance}();

		//if in deficit we repay amount and then withdraw
		if (deficit) {
			// 2a. if in deficit withdraw amount and repay it
			require(cToken.redeemUnderlying(amount) == 0, "!redeem_down");
			require(cToken.repayBorrow(IERC20(cToken.underlying()).balanceOf(address(this))) == 0, "!repay_down");
		} else {
			// 2b. if levering up borrow and deposit
			require(cToken.borrow(amount) == 0, "!borrow_up");
			require(cToken.mint(IERC20(cToken.underlying()).balanceOf(address(this))) == 0, "!mint_up");
		}
		// 3. Redeem collateral (ETH borrowed from DyDx) from Compound
		require(CETH.redeemUnderlying(wethBalance) == 0, "!redeem");
		// 4. Wrap ETH into WETH
		IWETH(WETH).deposit{value: address(this).balance}();

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
