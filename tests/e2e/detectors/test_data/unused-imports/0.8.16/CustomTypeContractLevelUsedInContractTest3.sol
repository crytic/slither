// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./CustomTypeContractLevel.sol";

contract CustomTypeContractLevelUsedInContractTest3
{
    modifier m()
    {
        CustomTypeContractLevel.CustomType ___;
        _;
    }
}