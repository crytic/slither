// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./CustomErrorTopLevel.sol";

contract CustomErrorTopLevelUsedInContractTest
{
    constructor()
    {
        f();
    }

    function f() private pure
    {
        revert err();
    }
}