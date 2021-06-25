pragma solidity >=0.5.7;
interface ISimpleSoloMargin {
    function operate(bytes memory) external;
    function getNumMarkets() external view returns (uint256);
    function getMarketTokenAddress(uint256 marketId) external view returns (address);
}