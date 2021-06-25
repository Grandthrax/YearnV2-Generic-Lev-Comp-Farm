pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;

interface IDydxHelpers{

    function getAccountInfo() external view returns (bytes memory);
    function getWithdrawAction(uint256 marketId, uint256 amount) external view returns (bytes memory);
    function getCallAction(bytes memory data) external view returns (bytes memory);
    function getDepositAction(uint256 marketId, uint256 amount) external view returns (bytes memory);
    function getSoloInput(uint256 marketId, uint256 depositAmount, bytes memory data, uint256 repayAmount) external view returns (bytes memory);
}