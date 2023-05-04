// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./EnumTopLevel.sol";

contract EnumTopLevelUsedInContractTest
{
    uint private v = uint(EnumTopLevel.__);
}