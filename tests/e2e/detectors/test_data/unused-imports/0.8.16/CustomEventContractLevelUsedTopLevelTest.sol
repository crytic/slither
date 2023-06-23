// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./CustomEventContractLevel.sol";

function f()
{
    emit CustomEventContractLevel.CustomEvent();
}

// dummy contract, so that "No contract were found ..." message is not being thrown by Slither
contract Dummy
{

}