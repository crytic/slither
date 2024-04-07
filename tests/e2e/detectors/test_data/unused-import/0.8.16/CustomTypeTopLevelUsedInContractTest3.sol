// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./CustomTypeTopLevel.sol";

contract CustomTypeTopLevelUsedInContractTest3
{
    modifier m()
    {
        CustomType v;
        _;
    }
}