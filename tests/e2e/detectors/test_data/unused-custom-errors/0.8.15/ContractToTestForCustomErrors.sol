// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.15;

error UnusedTopLevelErr();
error UsedTopLevelErr();

import "./ErrorLibConsumer.sol";

contract ParentContract {
    error UnusedParentErr();
    error UnusedParentErrWithArg(uint256 x);
    error UsedParentErr(address x);
    error UsedParentErrInChild(uint256 x);

    constructor() {
        new ErrorLibConsumer();
    }

    function x() public view {
        uint256 d = 7;
        if (msg.sender == address(0)) {
            d = 100;
            revert UsedParentErr(msg.sender);
        }
    }
}

contract ContractToTestForCustomErrors is ParentContract {
    function y() public {
        address f = msg.sender;
        (bool s,) = f.call("");
        if (!s) {
            revert UsedParentErrInChild(1);
        }
        revert UsedTopLevelErr();
    }

    function z() public {
        revert Lib.UsedLibErrorB(8);
    }
}
