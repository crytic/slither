pragma solidity >=0.4.16 <0.7.0;

contract SimpleWhile {
    uint public a;

    function f(uint input) public {
        while (input >= 0) {
            input = input - 1;
            a++;
        }
    }
}