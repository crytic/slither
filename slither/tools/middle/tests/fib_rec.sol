pragma solidity ^0.6.4;

contract Fib {
    function fib(uint n) public returns(uint res) {
        uint ret;
        if (n <= 1) {
            ret = n;
        } else {
            ret = Fib.fib(n - 1) + Fib.fib(n - 2);
        }
        return ret;
    }
}