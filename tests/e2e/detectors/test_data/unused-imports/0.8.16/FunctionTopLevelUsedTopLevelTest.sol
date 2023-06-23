// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./FunctionTopLevel.sol";

function f2()
{
    f();
}

contract Dummy_ // dummy contract needed, since otherwise f() call won't be analysed for some reason
{

}