// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./StructTopLevel.sol";

contract StructTopLevelUsedInContractTest
{
    struct CustomStruct
    {
        StructTopLevel __;
    }
}