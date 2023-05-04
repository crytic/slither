// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./CustomEventContractLevel.sol";

contract CustomEventContractLevelUsedInContractTest
{
    function f() public 
    {
        emit CustomEventContractLevel.CustomEvent();
    }
}