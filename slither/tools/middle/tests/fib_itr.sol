pragma solidity ^0.6.4;

contract Fib {
    function fib(uint n) public returns(uint res) {
        uint prev_prev_num;
        uint prev_num = 0;
        uint num = 1;
        for (uint i = 1; i < n; i++) {
            prev_prev_num = prev_num;
            prev_num = num;
            num = prev_prev_num + prev_num;
        }
        return num;
    }
}