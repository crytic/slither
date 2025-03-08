// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.15;

import "./CustomErrorsLib.sol";

contract ErrorLibConsumer {
    error UnusedErrorLibConsumerErr();
    error UsedErrorLibConsumerErr();

    constructor() {
        revert Lib.UsedLibErrorA();
    }

    function a() public pure {
        revert UsedErrorLibConsumerErr();
    }
}
