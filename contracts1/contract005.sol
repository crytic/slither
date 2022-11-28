// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ITarget {
    function exec() public {}
}

contract Reenter {
    uint x;

    function r1(ITarget target) public {
        if (x > 0) {
            target.exec();
            x = 0;
        }
    }

    function r2(ITarget target) public {
        if (x > 0) {
            for (uint i = 0; i < 1; i++) {
                target.exec();
            }
            x = 0;
        }
    }
}