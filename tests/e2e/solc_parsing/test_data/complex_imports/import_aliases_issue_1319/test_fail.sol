pragma solidity 0.5.12;

import {A as X, A as Y} from "./import.sol";

contract Z is X {
    function test() public pure returns (uint) {
        return 1;
    }
}