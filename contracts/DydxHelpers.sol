pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;

import "./Interfaces/DyDx/ISoloMargin.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";

contract DydxHelpers {
    using SafeMath for uint256;


    function getSoloInput(uint256 marketId, uint256 depositAmount, bytes memory data, uint256 repayAmount) external view returns (Account.Info[] memory accounts, Actions.ActionArgs[] memory actions){

        // 1. Withdraw $
        // 2. Call callFunction(...)
        // 3. Deposit back $
        Actions.ActionArgs[] memory operations = new Actions.ActionArgs[](3);

        operations[0] = getWithdrawAction(marketId, depositAmount);
        operations[1] = getCallAction(
            // Encode custom data for callFunction
            data
        );
        operations[2] = getDepositAction(marketId, repayAmount);

        Account.Info[] memory accountInfos = new Account.Info[](1);
        accountInfos[0] = getAccountInfo();

        return (accountInfos, operations);
    }


    function getAccountInfo() public view returns (Account.Info memory) {
        return Account.Info({owner: msg.sender, number: 1});
    }

    function getWithdrawAction(uint256 marketId, uint256 amount) public view returns (Actions.ActionArgs memory) {
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
                otherAddress: msg.sender,
                otherAccountId: 0,
                data: ""
            });
    }

    function getCallAction(bytes memory data) public view returns (Actions.ActionArgs memory) {
        return
            Actions.ActionArgs({
                actionType: Actions.ActionType.Call,
                accountId: 0,
                amount: Types.AssetAmount({sign: false, denomination: Types.AssetDenomination.Wei, ref: Types.AssetReference.Delta, value: 0}),
                primaryMarketId: 0,
                secondaryMarketId: 0,
                otherAddress: msg.sender,
                otherAccountId: 0,
                data: data
            });
    }

    function getDepositAction(uint256 marketId, uint256 amount) public view returns (Actions.ActionArgs memory) {
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
                otherAddress: msg.sender,
                otherAccountId: 0,
                data: ""
            });
    }
}