// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./CustomTypeContractLevel.sol";

CustomTypeContractLevel.CustomType constant __ = CustomTypeContractLevel.CustomType.wrap(0);

// dummy contract, so that "No contract were found ..." message is not being thrown by Slither
contract Dummy
{

}