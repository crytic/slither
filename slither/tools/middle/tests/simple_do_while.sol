pragma solidity >=0.4.16 <0.7.0;

contract SimpleDoWhile {
    uint public a;

    function f(uint input) public {
        uint i = 0;
        do {
            input = input * 2;
            input = input + 1;
        } while (i < input);
    }
}