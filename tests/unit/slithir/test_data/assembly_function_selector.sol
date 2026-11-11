// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract FunctionSelectorAsm {
    function writeLocal() public pure {
        function() external g;
        assembly {
            g.selector := 1
            g.address := 2
        }
    }

    function readParam(function() external pg) public pure returns (address a, bytes4 s) {
        assembly {
            a := pg.address
            s := pg.selector
        }
    }
}
