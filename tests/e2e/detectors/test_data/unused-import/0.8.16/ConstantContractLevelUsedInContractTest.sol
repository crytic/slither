// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./ConstantContractLevel.sol";

contract ConstantContractLevelUsedInContractTest
{
    uint private v = ConstantContractLevel.CONSTANT;
}