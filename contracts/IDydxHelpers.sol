pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;
import "./Interfaces/DyDx/ISoloMargin.sol";
interface IDydxHelpers{
    function getAccountInfo() external view returns (Account.Info memory);
    function getWithdrawAction(uint256 marketId, uint256 amount) external view returns (Actions.ActionArgs memory);
    function getCallAction(bytes memory data) external view returns (Actions.ActionArgs memory);
    function getDepositAction(uint256 marketId, uint256 amount) external view returns (Actions.ActionArgs memory);
}