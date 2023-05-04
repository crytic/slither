// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./CustomTypeContractLevel.sol";

contract CustomTypeContractLevelUsedInContractTest4
{
    struct CustomStruct
    {
        CustomTypeContractLevel.CustomType ___;
    }
}