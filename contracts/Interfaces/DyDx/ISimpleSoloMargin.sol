import {Account, Actions} from "./ISoloMargin.sol";
pragma experimental ABIEncoderV2;
pragma solidity >=0.5.7;
interface ISimpleSoloMargin {
    function operate(Account.Info[] memory accounts, Actions.ActionArgs[] memory actions) external;
    function getNumMarkets() external view returns (uint256);
    function getMarketTokenAddress(uint256 marketId) external view returns (address);
}