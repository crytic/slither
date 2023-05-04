// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./ConstantTopLevel.sol";

contract ConstantTopLevelUsedInContractTest
{
    uint private v = ConstantTopLevel;
}