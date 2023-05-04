// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./FunctionContractLevel.sol";

function f2() pure
{
    FunctionContractLevel.f();
}

// dummy contract, so that "No contract were found ..." message is not being thrown by Slither
contract Dummy
{

}