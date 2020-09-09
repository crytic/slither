pragma solidity >=0.4.16 <0.7.0;

contract Contract {
    uint public a;

    function f(uint input) public {
        a = (input == 5 ? 1 : 2);
    }
}