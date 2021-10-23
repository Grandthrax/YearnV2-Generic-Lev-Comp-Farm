pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/math/Math.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./Interfaces/Compound/CErc20I.sol";
import "./Interfaces/Compound/ComptrollerI.sol";
import "./Interfaces/DAI/IERC3156FlashLender.sol";
import "./Interfaces/DAI/IERC3156FlashBorrower.sol";

interface IUniswapAnchoredView {
    function price(string memory) external returns (uint256);
}

interface IERC20Extended is IERC20 {
    function decimals() external view returns (uint8);

    function name() external view returns (string memory);

    function symbol() external view returns (string memory);
}

library FlashMintLib {
    using SafeMath for uint256;
    event Leverage(uint256 amountRequested, uint256 requiredDAI, bool deficit, address flashLoan);

    uint256 private constant PRICE_DECIMALS = 1e6;
    uint256 private constant DAI_DECIMALS = 1e18;
    uint256 private constant COLLAT_DECIMALS = 1e18;
    address public constant DAI = 0x6B175474E89094C44Da98b954EedeAC495271d0F;
    address public constant CDAI = 0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643;
    address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address private constant WBTC = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599;
    ComptrollerI private constant COMPTROLLER = ComptrollerI(0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B);
    address public constant LENDER = 0x1EB4CF3A948E7D72A198fe073cCb8C7a948cD853;
    bytes32 public constant CALLBACK_SUCCESS = keccak256("ERC3156FlashBorrower.onFlashLoan");

    function doFlashMint(
        bool deficit,
        uint256 amountDesired,
        address want,
        uint256 collatRatioDAI
    ) public returns (uint256) {
        if (amountDesired == 0) {
            return 0;
        }

        // calculate amount of DAI we need
        (uint256 requiredDAI, uint256 amountWant) = getFlashLoanParams(want, amountDesired, collatRatioDAI);

        bytes memory data = abi.encode(deficit, amountWant);
        uint256 _fee = IERC3156FlashLender(LENDER).flashFee(DAI, amountWant);
        // Check that fees have not been increased without us knowing
        require(_fee == 0);
        uint256 _allowance = IERC20(DAI).allowance(address(this), address(LENDER));
        if (_allowance < requiredDAI) {
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

    function getFlashLoanParams(
        address want,
        uint256 amountDesired,
        uint256 collatRatioDAI
    ) internal returns (uint256 requiredDAI, uint256 amountWant) {
        uint256 priceDAIWant;
        uint256 decimalsDifference;
        (priceDAIWant, decimalsDifference, requiredDAI) = getPriceDAIWant(want, amountDesired, collatRatioDAI);
        amountWant = amountDesired;

        // If the cap for flashminting is reduced, we may hit maximum. To avoid reverts in that case we handle the edge case
        uint256 _maxFlashLoan = maxLiquidity();
        if (requiredDAI > _maxFlashLoan) {
            requiredDAI = _maxFlashLoan.mul(9800).div(10_000); // use 98% of total liquidity available
            if (address(want) == address(DAI)) {
                amountWant = requiredDAI;
            } else {
                amountWant = requiredDAI.mul(collatRatioDAI).mul(PRICE_DECIMALS).div(priceDAIWant).div(COLLAT_DECIMALS).div(decimalsDifference);
            }
        }
    }

    function getPriceDAIWant(
        address want,
        uint256 amountDesired,
        uint256 collatRatioDAI
    )
        internal
        returns (
            uint256 priceDAIWant,
            uint256 decimalsDifference,
            uint256 requiredDAI
        )
    {
        if (want == DAI) {
            requiredDAI = amountDesired;
            priceDAIWant = PRICE_DECIMALS; // 1:1
            decimalsDifference = 1; // 10 ** 0
        } else {
            // NOTE: want decimals need to be <= 18. otherwise this will break
            uint256 wantDecimals = 10**uint256(IERC20Extended(want).decimals());
            decimalsDifference = DAI_DECIMALS.div(wantDecimals);
            priceDAIWant = getOraclePrice(DAI).mul(PRICE_DECIMALS).div(getOraclePrice(want));
            // requiredDAI = desiredWantInDAI / COLLAT_RATIO_DAI
            // desiredWantInDAI = (desiredWant / priceDAIWant)
            // NOTE: decimals need adjustment (e.g. BTC: 8 / ETH: 18)
            requiredDAI = amountDesired.mul(PRICE_DECIMALS).mul(COLLAT_DECIMALS).mul(decimalsDifference).div(priceDAIWant).div(collatRatioDAI);
        }
    }

    function getOraclePrice(address token) internal returns (uint256) {
        string memory symbol;
        // Symbol for WBTC is BTC in oracle
        if (token == WBTC) {
            symbol = "BTC";
        } else if (token == WETH) {
            symbol = "ETH";
        } else {
            symbol = IERC20Extended(token).symbol();
        }
        IUniswapAnchoredView oracle = IUniswapAnchoredView(COMPTROLLER.oracle());
        return oracle.price(symbol);
    }

    function loanLogic(
        bool deficit,
        uint256 amountDAI,
        uint256 amount,
        CErc20I cToken
    ) public returns (bytes32) {
        // if want is not DAI, we provide flashminted DAI to borrow want and be able to lever up/down
        // if want is DAI, we use it directly to lever up/down
        bool isDai;
        // We check if cToken is DAI to save a couple of unnecessary calls
        if (address(cToken) == address(CDAI)) {
            isDai = true;
            require(amountDAI == amount, "!amounts");
        }
        uint256 daiBal = IERC20(DAI).balanceOf(address(this));
        if (deficit) {
            if (!isDai) {
                require(CErc20I(CDAI).mint(daiBal) == 0, "!mint_flash");
                require(cToken.redeemUnderlying(amount) == 0, "!redeem_down");
            }
            //if in deficit we repay amount and then withdraw
            require(cToken.repayBorrow(IERC20(cToken.underlying()).balanceOf(address(this))) == 0, "!repay_down");
            require(CErc20I(CDAI).redeemUnderlying(amountDAI) == 0, "!redeem");
        } else {
            // if levering up borrow and deposit
            require(CErc20I(CDAI).mint(daiBal) == 0, "!mint_flash");
            require(cToken.borrow(amount) == 0, "!borrow_up");
            if (!isDai) {
                require(cToken.mint(IERC20(cToken.underlying()).balanceOf(address(this))) == 0, "!mint_up");
                require(CErc20I(CDAI).redeemUnderlying(amountDAI) == 0, "!redeem");
            }
        }
        return CALLBACK_SUCCESS;
    }
}
