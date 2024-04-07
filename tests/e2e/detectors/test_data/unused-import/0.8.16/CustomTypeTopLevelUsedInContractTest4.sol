// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./CustomTypeTopLevel.sol";

contract CustomTypeTopLevelUsedInContractTest4
{
    struct CustomStruct
    {
        CustomType ___;
    }
}