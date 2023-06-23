// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./StructTopLevel.sol";

struct CustomStruct
{
    StructTopLevel __;
}

// dummy contract, so that "No contract were found ..." message is not being thrown by Slither
contract Dummy_
{

}
