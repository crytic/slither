pragma solidity 0.5.12;

import {A} from "./import.sol";

contract Z is A {
    function test() public pure returns (uint) {
        return 1;
    }
}