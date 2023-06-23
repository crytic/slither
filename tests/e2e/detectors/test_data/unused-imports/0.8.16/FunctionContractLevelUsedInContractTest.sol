// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./FunctionContractLevel.sol";

contract FunctionContractLevelUsedInContractTest
{
    function f2() private pure
    {
        FunctionContractLevel.f();
    }
}