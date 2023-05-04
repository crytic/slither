// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./Contract.sol";

Contract constant c = Contract(address(0x0));

// dummy contract, so that "No contract were found ..." message is not being thrown by Slither
contract Dummy
{

}