// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./StructContractLevel.sol";

contract StructContractLevelUsedInContractTest
{
    struct CustomStruct
    {
        StructContractLevel.CustomStruct __;
    }
}
