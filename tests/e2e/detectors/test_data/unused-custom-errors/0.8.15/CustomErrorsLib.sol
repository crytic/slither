// SPDX-License-Identifier: Unlicense
pragma solidity 0.8.15;

library Lib {
    error UnusedLibError();
    error UsedLibErrorA();
    error UsedLibErrorB(uint256 x);
}