// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.16;

import "./B.sol";

contract C
{
    constructor()
    {
        A.a();
    }
}