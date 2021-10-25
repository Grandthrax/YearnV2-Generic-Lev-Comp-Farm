// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "./Interfaces/DAI/IERC3156FlashLender.sol";
import "./Interfaces/DAI/IERC3156FlashBorrower.sol";

contract ReentryTest {
    address public constant LENDER = 0x1EB4CF3A948E7D72A198fe073cCb8C7a948cD853;
    address public constant DAI = 0x6B175474E89094C44Da98b954EedeAC495271d0F;

    function callOnFlashLoan(address strategy) public {
        address initiator = strategy;
        address token = DAI;
        uint256 amount = 0;
        uint256 fee = 0;
        bytes memory data = abi.encode(false, 0);

        IERC3156FlashBorrower(strategy).onFlashLoan(initiator, token, amount, fee, data);
    }
}
