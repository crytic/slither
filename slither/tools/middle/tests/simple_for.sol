pragma solidity >=0.4.16 <0.7.0;

contract SimpleFor {
    uint public a;

    function f(uint input) public {
        for (uint i = 0; i < input; i++) {
            a++;
        }
    }
}