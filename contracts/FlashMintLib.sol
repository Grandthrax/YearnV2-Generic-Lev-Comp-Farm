pragma solidity 0.6.12; 
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./Interfaces/Compound/CErc20I.sol";
import "./Interfaces/Compound/ComptrollerI.sol";
import "./Interfaces/DAI/IERC3156FlashLender.sol";
import "./Interfaces/DAI/IERC3156FlashBorrower.sol";

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

library FlashMintLib {
	using SafeMath for uint256;
	event Leverage(uint256 amountRequested, uint256 amountGiven, bool deficit, address flashLoan);

	uint256 private constant PRICE_DECIMALS = 1e6;
	uint256 private constant DAI_DECIMALS = 1e18;
	uint256 private constant COLLAT_RATIO_DAI = 0.74 ether;
    address public constant DAI = 0x6B175474E89094C44Da98b954EedeAC495271d0F;
    address public constant CDAI = 0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643;
	address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
	address private constant WBTC = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599;
	ComptrollerI private constant COMP = ComptrollerI(0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B);
    address public constant LENDER = 0x1EB4CF3A948E7D72A198fe073cCb8C7a948cD853;
    bytes32 public constant CALLBACK_SUCCESS = keccak256("ERC3156FlashBorrower.onFlashLoan");

    function doFlashMint(bool deficit, uint256 amountDesired, address want, uint256 maxFee) public returns (uint256) {
        if(amountDesired == 0) {
            return 0;
        }

        // calculate amount of ETH we need
        (uint256 requiredDAI, uint256 amountWant) = getFlashLoanParams(want, amountDesired);

        bytes memory data = abi.encode(deficit, amountWant);
        uint256 _allowance = IERC20(DAI).allowance(address(this), address(LENDER));
        uint256 _fee = IERC3156FlashLender(LENDER).flashFee(DAI, amountWant);
        // Check that fees have not been increased without us knowing
        require(_fee <= _calcFee(requiredDAI, maxFee));
        uint256 _repayment = requiredDAI.add(_fee);
        if(_allowance < _repayment) {
            IERC20(DAI).approve(address(LENDER), 0);
            IERC20(DAI).approve(address(LENDER), type(uint256).max);
        }
        IERC3156FlashLender(LENDER).flashLoan(IERC3156FlashBorrower(address(this)), DAI, requiredDAI, data);

        emit Leverage(amountDesired, requiredDAI, deficit, address(LENDER));

        return amountWant;
    }

    function maxLiquidity() public view returns (uint256) {
        return IERC3156FlashLender(LENDER).maxFlashLoan(DAI);
    }

    function _calcFee(uint256 amount, uint256 maxFee) internal view returns (uint256) {
        return amount.mul(maxFee).div(1e18);
    }

	function getFlashLoanParams(address want, uint256 amountDesired) internal returns (uint256 requiredDAI, uint256 amountWant) {
		(uint256 priceDAIWant, uint256 decimalsDifference, uint256 _requiredDAI) = getPriceDAIWant(want, amountDesired);
		// to avoid stack too deep	
		requiredDAI = _requiredDAI;
		amountWant = amountDesired;
		// Not enough want in DAI. So we take all we can
		uint256 _maxFlashLoan = maxLiquidity();
        if(requiredDAI > _maxFlashLoan) {
            requiredDAI = _maxFlashLoan;
            amountWant = requiredDAI.mul(COLLAT_RATIO_DAI).mul(PRICE_DECIMALS).div(priceDAIWant).div(1e18).div(decimalsDifference);
        }
	}

	function getPriceDAIWant(address want, uint256 amountDesired) internal returns (uint256 priceDAIWant, uint256 decimalsDifference, uint256 requiredDAI) {
		uint256 wantDecimals = 10 ** uint256(IERC20Extended(want).decimals());
		decimalsDifference = DAI_DECIMALS > wantDecimals ? DAI_DECIMALS.div(wantDecimals) : wantDecimals.div(DAI_DECIMALS);
		if(want == DAI) {
			requiredDAI = amountDesired.mul(1e18).div(COLLAT_RATIO_DAI);
			priceDAIWant = 1e6; // 1:1
		} else {
			priceDAIWant = getOraclePrice(DAI).mul(PRICE_DECIMALS).div(getOraclePrice(want));
			// requiredDAI = desiredWantInDAI / COLLAT_RATIO_DAI
			// desiredWantInDAI = (desiredWant / priceDAIWant)
			// NOTE: decimals need adjustment (e.g. BTC: 8 / ETH: 18)
			requiredDAI = amountDesired.mul(PRICE_DECIMALS).mul(1e18).mul(decimalsDifference).div(priceDAIWant).div(COLLAT_RATIO_DAI);
		}
	}

	function getOraclePrice(address token) internal returns (uint256) {
		string memory symbol;
		// Symbol for WBTC is BTC in oracle
		if(token == WBTC) {
			symbol = "BTC";
		} else if (token == WETH) {
			symbol = "ETH";
		} else {
            symbol = IERC20Extended(token).symbol();
        }
		IUniswapAnchoredView oracle = IUniswapAnchoredView(COMP.oracle());
		return oracle.price(symbol);
	}

	function loanLogic(
		bool deficit,
        uint256 amountDAI,
		uint256 amount,
		CErc20I cToken
	) 
        public returns (bytes32)
    {
		// 1. Deposit DAI in Compound as collateral
		require(CErc20I(CDAI).mint(amountDAI) == 0, "!mint_flash");

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
		// 3. Redeem collateral (flashminted DAI) from Compound
		require(CErc20I(CDAI).redeemUnderlying(amountDAI) == 0, "!redeem");

        return CALLBACK_SUCCESS;
	}
}

