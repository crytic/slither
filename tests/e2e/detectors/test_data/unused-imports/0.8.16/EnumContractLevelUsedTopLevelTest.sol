// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./EnumContractLevel.sol";

uint constant __ = uint(EnumContractLevel.CustomEnum.__);

// dummy contract, so that "No contract were found ..." message is not being thrown by Slither
contract Dummy
{

}