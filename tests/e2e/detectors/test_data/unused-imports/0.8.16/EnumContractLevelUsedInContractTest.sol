// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./EnumContractLevel.sol";

contract EnumContractLevelUsedInContractTest
{
    uint private v  = uint(EnumContractLevel.CustomEnum.__);
}