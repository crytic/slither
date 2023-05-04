// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./CustomTypeTopLevel.sol";

struct CustomTypeTopLevelUsedTopLevelTest1
{
    CustomType __;
}

// dummy contract, so that "No contract were found ..." message is not being thrown by Slither
contract Dummy_
{

}
