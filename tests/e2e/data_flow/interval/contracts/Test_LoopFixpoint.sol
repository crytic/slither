// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Test_LoopFixpoint {
    function test_multiple_back_edges() public pure returns (uint256) {
        uint256 i = 0;
        uint256 sum = 0;
        while (i < 10) {
            if (i % 2 == 0) {
                i += 1;
                sum += i;
                continue;
            }
            i += 2;
            sum += i;
            continue;
        }
        return sum;
    }

    function test_nested_loops() public pure returns (uint256) {
        uint256 sum = 0;
        for (uint256 i = 0; i < 3; i++) {
            for (uint256 j = 0; j < 2; j++) {
                sum += i + j;
            }
        }
        return sum;
    }
}
